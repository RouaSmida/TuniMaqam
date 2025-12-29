# Dockerfile for TuniMaqam
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# System deps 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose Flask/gunicorn port
EXPOSE 8000

# Environment defaults (override in docker-compose or docker run)
ENV FLASK_ENV=production
ENV FLASK_APP=app.py


# Run with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:create_app()"]
