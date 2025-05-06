# Use a slim Python image
FROM python:3.11-slim

# Set environment variables to avoid .pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (for aiohttp)
RUN apt-get update && apt-get install -y build-essential && apt-get clean

# Copy only requirement files first for caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . /app/

# Expose port 3005
EXPOSE 3005

# Command to run app
CMD ["uvicorn", "weather_mcp_server_api:app", "--host", "0.0.0.0", "--port", "3005"]
