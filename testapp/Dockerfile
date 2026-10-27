# Use a small, specific base image tag
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy dependency files first to avoid unnecessary layering
COPY requirements.txt .

# Install all dependencies
RUN pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Run the Flask application
CMD ["python", "app.py"]
