FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .
COPY frontend/ ./static/

# Make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Expose both ports
EXPOSE 8000 8080

# Start both services
CMD ["./start.sh"]