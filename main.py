import logging
import os

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Rate Limit in requests per Minute(defined in environment variable)
RATE_LIMIT = os.getenv("RATE_LIMIT", "")

# Ensure there's rate limit set
if not RATE_LIMIT or RATE_LIMIT == [""]:
    logger.error("No rate limit set. Define RATE_LIMIT environment variable.")
    raise Exception("No rate limit set. Define RATE_LIMIT environment variable.")


# Initialize the rate limiter
rate_limit = f"{RATE_LIMIT}/minute"
limiter = Limiter(key_func=get_remote_address, default_limits=[rate_limit])

logger.info(f"Rate limit set to: {rate_limit}")

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Load configuration from YAML file
def load_config():
    with open("/app/config/config.yml", "r") as file:
        return yaml.safe_load(file)


config = load_config()
logger.info(f"Loaded configuration: {config}")


# Middleware to restrict access based on IP address
class IPWhitelistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips):
        super().__init__(app)
        self.allowed_ips = allowed_ips

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if not self.allowed_ips or client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access forbidden: Your IP address is not allowed"},
            )
        response = await call_next(request)
        return response


# List of allowed IP addresses (defined in environment variables)
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",")

# Ensure there's at least one allowed IP or raise an exception
if not ALLOWED_IPS or ALLOWED_IPS == [""]:
    logger.error(
        "No allowed IP addresses set. Define ALLOWED_IPS environment variable."
    )
    raise Exception(
        "No allowed IP addresses set. Define ALLOWED_IPS environment variable."
    )


logger.info(f"Allowed Client IPs: {ALLOWED_IPS}")

# Enable Middleware to restrict access and rate limit of requests
app.add_middleware(SlowAPIASGIMiddleware)
app.add_middleware(IPWhitelistMiddleware, allowed_ips=ALLOWED_IPS)


@app.get("/{path:path}")
async def get_to_post(path: str, request: Request):
    # Construct the original GET URL
    get_url = f"/{path}".rstrip("/")
    logger.info(f"Received GET request for path: {get_url}")

    # Check if the GET URL has a corresponding POST URL
    if get_url in config["endpoints"]:
        target_config = config["endpoints"][get_url]
        post_url = target_config["post_url"]
        target_host = target_config["target_host"]
        auth_method = target_config.get("auth_method")

        headers = {}

        # Handle different authentication methods
        if auth_method in ["token", "bearer"]:
            api_key_env = target_config.get("api_key_env")
            if api_key_env:
                api_key = os.getenv(api_key_env)
                if api_key and auth_method == "token":
                    headers["Authorization"] = f"Token {api_key}"
                elif api_key and auth_method == "bearer":
                    headers["Authorization"] = f"Bearer {api_key}"
                else:
                    logger.error(
                        f"API key not found in environment variable {api_key_env}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"API key not found in environment variable {api_key_env}",
                    )
        elif auth_method == "basic":
            username_env = target_config.get("username_env")
            password_env = target_config.get("password_env")
            if username_env and password_env:
                username = os.getenv(username_env)
                password = os.getenv(password_env)
                if username and password:
                    headers["Authorization"] = httpx.BasicAuth(
                        username, password
                    )._auth_header
                else:
                    logger.error(
                        f"Basic auth credentials not found in environment variables {username_env} and/or {password_env}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Basic auth credentials not found in environment variables {username_env} and/or {password_env}",
                    )

        # Extract query parameters and convert them to a dictionary
        query_params = dict(request.query_params)
        logger.info(f"Query parameters: {query_params}")

        try:
            # Perform the POST request with the query parameters as JSON payload and the authentication headers if provided
            async with httpx.AsyncClient(base_url=target_host) as client:
                response = await client.post(
                    post_url, json=query_params, headers=headers
                )

            # Return the response from the POST request with the status code
            return JSONResponse(
                content=response.json(), status_code=response.status_code
            )
            logger.info("query send")
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors
            logger.info("HTTPStatusError")
            logger.error(f"HTTP error: {e}")
            return JSONResponse(
                status_code=e.response.status_code,
                content={"detail": e.response.json()},
            )
        except httpx.RequestError as e:
            # Handle request errors
            logger.info("RequestError")
            logger.error(f"Request error: {e}")
            return JSONResponse(status_code=500, content={"detail": str(e)})
        except Exception as e:
            # Handle request errors
            logger.info("ExceptionError")
            logger.error(f"Exception error: {e}")
            return Response(status_code=response.status_code, content=response.content)

    else:
        logger.error(f"No mapping found for GET endpoint: {get_url}")
        raise HTTPException(
            status_code=404, detail="No mapping found for this GET endpoint"
        )


# Example POST endpoint to test the conversion
# Not required if Mockserver is used in development
@app.post("/example-post")
async def example_post(payload: dict):
    return {"message": "Received POST request", "payload": payload}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )
