#!/bin/bash
export PORT=${PORT:-8000}

# Run Gunicorn with Gevent WebSocket Worker
exec gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
    -w 1 -b 0.0.0.0:$PORT app:app
