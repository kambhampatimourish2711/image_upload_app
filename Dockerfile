# Use a lightweight Python image
FROM python:3.9-slim

# Environment settings to ensure clean execution
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app/

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code to the container
COPY . /app/

# Expose the default port for the application
EXPOSE 8080

# Optimized Gunicorn command with fewer workers and threads
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "120", "main:app"]
