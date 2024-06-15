# Use the official Python image based on Alpine Linux for minimal footprint
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Get2Post GW app file
COPY main.py .

# Expose the port Get2Post GW will run on
EXPOSE 8888

# Command to run the Get2Post GW app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]
