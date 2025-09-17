# Use an official lightweight Python image (better compatibility than Alpine for wheels)
FROM python:3.12-slim AS runtime

# Set environment (no .pyc files, unbuffered logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Create working directory
WORKDIR /app

# Install system build deps only when needed (many pure-python libs so keep minimal)
# Uncomment and extend if a package later needs build tools (e.g. gcc)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy only requirements first (better cache)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Ensure instance folder exists for SQLite DB
RUN mkdir -p instance && chmod 755 instance

# Create non-root user
RUN useradd -ms /bin/bash appuser
USER appuser

# Expose app port
EXPOSE 8000

# Healthcheck (simple TCP check)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8000)); s.close()" || exit 1

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app", "--workers", "3", "--threads", "4", "--timeout", "60"]
