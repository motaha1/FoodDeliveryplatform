FROM python:3.12-slim AS runtime


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app


WORKDIR /app


RUN pip install --upgrade pip


COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .


RUN mkdir -p instance && chmod 755 instance


RUN useradd -ms /bin/bash appuser
USER appuser


EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8000)); s.close()" || exit 1


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app", "--workers", "3", "--threads", "4", "--timeout", "60"]
