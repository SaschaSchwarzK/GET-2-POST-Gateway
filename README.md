# GET2POST Gateway
## Overview
The GET2POST Gateway is a FastAPI application designed to convert incoming GET requests into POST requests. It allows you to configure mappings between GET endpoints and target POST endpoints, including support for various authentication methods. This gateway is useful for scenarios where you need to interface with APIs that only accept POST requests, but you have clients that can only send GET requests.

## Purpose
The primary motivation behind developing the GET2POST Gateway was the necessity to convert custom links in NetBox to POST requests. NetBox, a popular open-source IP address management (IPAM) and data center infrastructure management (DCIM) tool, primarily supports GET requests for its custom link functionalities. However, many modern APIs, including those used for automation and orchestration, require POST requests to handle data modifications or triggers. This gateway seamlessly bridges that gap, enabling NetBox custom links to interact with such APIs without changing their fundamental operation.

## Disclaimer

The usage of this application is at your own risk. Please carefully consider the security implications and potential risks before deploying or using this API gateway in a production environment.

> Read the security considerations carefully!

By using this API gateway, you acknowledge and accept these considerations. The developers and maintainers of this project disclaim any liability for misuse or any damages resulting from the usage of this application.


## Features
* **GET to POST Conversion**: Converts GET requests into POST requests and forwards them to the target endpoint.
* **Configurable Mappings**: Easily configure mappings between GET endpoints and POST endpoints through a YAML configuration file.
* **Authentication Support**: Supports Bearer token and Basic authentication methods.
* **Environment Variables for Secrets**: Stores sensitive information like API keys and passwords in environment variables for security.
* **Parameters to Payload**: URL parameters will be converted into JSON Payload
* **Rate Limiting**: Limit the number of request per minute
* **Error Handling**: Returns appropriate status codes and error messages to the client if something goes wrong.

## Security Considerations
### Authentication Secrets in URL Parameters
#### Risks:
Transferring authentication secrets (such as API keys, tokens, or passwords) as URL parameters poses significant security risks:

* **Exposure in Logs**: URLs can be logged by various systems (e.g., web servers, proxies, or browser history), leading to unintended exposure of sensitive information.
* **Cache Risks**: Some intermediate proxies or web caches might store URLs, including the secrets, making them accessible to unauthorized parties.
* **Referrer Header Leak**: URLs with sensitive information can be exposed through the Referer header when a user clicks on a link to another website.
* **Solution**:
Instead of passing secrets in URLs, authentication secrets are stored in environment variables on the GET2POST GW. 

This approach ensures:

* **Reduced Exposure**: Secrets are not exposed in URLs, logs, or referrer headers.
* **Secure Management**: Environment variables can be securely managed and injected into the application at runtime without hardcoding them into the codebase.
* **Simplified Configuration**: Secrets can be easily rotated and managed across different environments (e.g., development, staging, production) without altering the application code.

### Limiting Access to the Gateway
#### Risks of Unrestricted Access:
Allowing unrestricted access to the gateway can lead to:

* **Unauthorized Use**: Unauthorized individuals can trigger POST requests, potentially leading to misuse or abuse of backend services.
* **Increased Attack Surface**: A wider range of IP addresses can increase the likelihood of attacks, such as brute force attempts, Denial of Service (DoS), or exploitation of vulnerabilities.

#### Importance of IP Whitelisting:
By locking down the source IPs and limiting access to trusted clients, we can:

* **Enhance Security**: Restrict access to known and trusted IP addresses, reducing the risk of unauthorized access and attacks.
* **Control Access**: Ensure that only designated systems or users can interact with the gateway, maintaining tighter control over the API usage.
* **Reduce Exposure**: Minimize the potential attack surface by excluding unknown or untrusted sources from interacting with the gateway.


### Remaining Risk: Authenticated POST Request Triggering
#### Risk Description:
While storing authentication secrets in environment variables and restricting access to the Get2Post Gateway by IP address enhances security, a residual risk remains. Anyone with access to the Get2Post Gateway can trigger an authenticated POST request. This means that unauthorized users or systems can potentially initiate actions that utilize the stored authentication credentials.

**Potential Impact**:
* **Unauthorized Actions**: Authorized users may trigger POST requests unintentionally or maliciously, leading to undesired actions on the target system.
* **Abuse of Privileges**: If the POST requests are not adequately controlled, users might abuse their access to perform actions beyond their intended scope.
* **Security Breach**: Sensitive operations could be executed without additional safeguards, potentially compromising data or system integrity.

**Mitigation Strategies**:
Limiting POST Request Actions:
To mitigate these risks, the actions that can be performed via the authenticated POST requests should be limited to non-harmful activities. This includes:

* **Read-Only Operations**: Where possible, restrict POST requests to operations that do not alter data or system state.
* **Non-Critical Updates**: Ensure that POST requests are limited to actions that do not have significant security or operational implications (e.g., minor data updates or logging).
* **Controlled Environments**: Use the gateway in environments where actions are monitored and can be quickly reverted if necessary.

**Additional Security Measures**:
* **Rate Limiting**: Set the default for the rate limiting to a value that is required for the use case, but low enough to prevent abuse and reduce the risk of Denial of Service (DoS) attacks.
* **Detailed Logging**: Maintain comprehensive logs of all requests and actions performed via the gateway to enable auditing and monitoring.
* **Role-Based Access Control (RBAC)**: If applicable, implement RBAC to ensure that user ID used to make POST requests only have permissions to trigger POST requests relevant to their role.
* **Regular Reviews**: Periodically review and update the configuration and access controls to adapt to changing security requirements.

By implementing these additional measures and limiting the scope of actions that can be triggered via the Get2Post Gateway, we can further reduce the potential impact of this residual risk. But a potential risk will remain, even with all those mitigations in place.

## Configuration
The gateway uses a YAML file for configuration. This file should be mounted into the container at runtime. Below is an example of the configuration file (config.yml):

    endpoints:
      /example-get:
        post_url: /example-post
        target_host: http://localhost:8000
        auth_method: bearer
        api_key_env: API_KEY_ENV_VAR
      /another-get:
        post_url: /another-post
        target_host: http://another-host:8000
        auth_method: basic
        username_env: BASIC_AUTH_USERNAME
        password_env: BASIC_AUTH_PASSWORD

## Environment Variables
Environment variables need to be set, depending on the authentication method used:

    API_KEY_ENV_VAR: The environment variable storing the API key for Bearer token authentication.
    BASIC_AUTH_USERNAME: The environment variable storing the username for Basic authentication.
    BASIC_AUTH_PASSWORD: The environment variable storing the password for Basic authentication.
    
Environment variables need to be set for the app to function:

    ALLOWED_IPS: The environment variable storing the allowed source IPs separated by comma.
    RATE_LIMIT: The environment variable storing allowed number of requests per minute.


## Usage
### Set Environment Variables
Ensure that your .env file contains the necessary environment variables if authentication is required for the POST requests:

    API_KEY_ENV_VAR=your_api_key
    BASIC_AUTH_USERNAME=your_username
    BASIC_AUTH_PASSWORD=your_password

### Build the Container

    docker compose build --no-cache

### Configuration

Make sure to edit the ./config/config.yml to your needs.
    
### Run the Container

    docker compose up -d
    
### Test

#### Example POST Endpoint
The application also includes an example POST endpoint to test the conversion:

    @app.post("/example-post")
    async def example_post(payload: dict):
        return {"message": "Received POST request", "payload": payload}

#### Sending Requests
To send a GET request that will be converted to a POST request:

    $ curl -X GET "http://localhost:8888/example-get?test=1"
    
This request will be converted and forwarded to http://localhost:8000/example-post with the query parameters sent as JSON payload.

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
    100    58  100    58    0     0   2584      0 --:--:-- --:--:-- --:--:--  2761{"message":"Received POST request","payload":{"test":"1"}}
    

## Error Handling
If the gateway encounters an error (e.g., missing API key, request failure), it will return a JSON response with the appropriate status code and an error message.

In the case of himit the rate limit and error message will be returned.

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    47  100    47    0     0  14669      0 --:--:-- --:--:-- --:--:-- 23500{"error":"Rate limit exceeded: 1 per 1 minute"}
    
If an endpoint cannot be mapped there will be an error messages as well.

      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    51  100    51    0     0  16526      0 --:--:-- --:--:-- --:--:-- 25500{"detail":"No mapping found for this GET endpoint"}


## Logging
The application logs key events and errors to help with debugging and monitoring.

    Attaching to get2post_gateway
    get2post_gateway  | INFO:main:Rate limit set to: 1/minute
    get2post_gateway  | INFO:main:Loaded configuration: {'endpoints': {'/example-get': {'post_url': '/example-post', 'target_host': 'http://127.0.0.1:8888', 'auth_method': 'bearer', 'api_key_env': 'API_KEY_ENV_VAR'}, '/another-get': {'post_url': '/another-post', 'target_host': 'http://127.0.0.1:8888', 'auth_method': 'basic', 'username_env': 'BASIC_AUTH_USERNAME', 'password_env': 'BASIC_AUTH_PASSWORD'}}}
    get2post_gateway  | INFO:main:Allowed Client IPs: ['127.0.0.1', '172.22.0.1']
    get2post_gateway  | INFO:     Started server process [1]
    get2post_gateway  | INFO:     Waiting for application startup.
    get2post_gateway  | INFO:     Application startup complete.
    get2post_gateway  | INFO:     Uvicorn running on http://0.0.0.0:8888 (Press CTRL+C to quit)
    get2post_gateway  | INFO:main:Received GET request for path: /example-get
    get2post_gateway  | INFO:main:Query parameters: {'test': '1'}
    get2post_gateway  | INFO:     127.0.0.1:35932 - "POST /example-post HTTP/1.1" 200 OK
    get2post_gateway  | INFO:httpx:HTTP Request: POST http://127.0.0.1:8888/example-post "HTTP/1.1 200 OK"
    get2post_gateway  | INFO:     172.22.0.1:35922 - "GET /example-get?test=1 HTTP/1.1" 200 OK
    get2post_gateway  | WARNING:slowapi:ratelimit 1 per 1 minute (172.22.0.1) exceeded at endpoint: /example-get
    get2post_gateway  | INFO:     172.22.0.1:35934 - "GET /example-get?test=1 HTTP/1.1" 429 Too Many Requests
    get2post_gateway  | INFO:main:Received GET request for path: /exampleget
    get2post_gateway  | ERROR:main:No mapping found for GET endpoint: /exampleget
    get2post_gateway  | INFO:     172.22.0.1:53950 - "GET /exampleget?test=1 HTTP/1.1" 404 Not Found


## License
This project is licensed under the MIT License.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss any changes.

## Contact
For questions or support, please open an issue on the GitHub repository.
    
