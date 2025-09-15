FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .
COPY frontend/ /app/static/

# Make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Create logs directory
RUN mkdir -p /app/logs

# Expose both ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health && curl -f http://localhost:8080/ || exit 1

# Use start script as entrypoint
CMD ["/app/start.sh"]