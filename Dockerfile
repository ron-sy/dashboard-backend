FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app
# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
# Set environment variables
ENV PORT=8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser
# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "src.app:app"]
