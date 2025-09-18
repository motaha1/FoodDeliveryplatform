from flask import Blueprint, Response, request, jsonify, stream_with_context
import json, time
from implementations.feature4_restaurant_notifications.services.redis_client import get_redis
import redis.exceptions  # added for error handling

notification_bp = Blueprint('restaurant_notifications', __name__, url_prefix='/api/v1')

# Very simple single channel
ORDERS_CHANNEL = 'orders'
PING_INTERVAL = 15  # keep-alive comment every 15s
RETRY_MS = 3000     # client reconnection hint

@notification_bp.route('/orders/stream')
def simple_orders_stream():
    """Simple SSE endpoint streaming every published message from Redis channel 'orders'.
    Each published message is sent verbatim as one SSE data block.
    """
    # Graceful Redis connection error handling
    try:
        redis_client = get_redis()
        # Test connection
        redis_client.ping()
        pubsub = redis_client.pubsub()
        pubsub.subscribe(ORDERS_CHANNEL)
    except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError) as e:
        # Return 503 Service Unavailable with better error handling
        return jsonify({
            'success': False, 
            'error': 'redis_unavailable',
            'message': 'Redis service is not available. Please check Redis server.'
        }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'service_error', 
            'message': f'Service error: {str(e)}'
        }), 503

    def event_stream():
        last_ping = time.time()
        # Tell browser how long to wait before auto-reconnect
        yield f'retry: {RETRY_MS}\n\n'
        try:
            while True:
                try:
                    message = pubsub.get_message(timeout=1.0)
                except redis.exceptions.ConnectionError:
                    yield 'event: error\ndata: {"error":"redis_lost","message":"Lost Redis connection"}\n\n'
                    break
                now = time.time()
                if now - last_ping >= PING_INTERVAL:
                    # Comment line acts as keep-alive
                    yield ': ping\n\n'
                    last_ping = now
                if message and message.get('type') == 'message':
                    data = message['data']  # already a string (decode_responses=True)
                    # One SSE event (default event type 'message')
                    yield f'data: {data}\n\n'
        finally:
            try: pubsub.unsubscribe(ORDERS_CHANNEL)
            except Exception: pass
            try: pubsub.close()
            except Exception: pass

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    }
    return Response(stream_with_context(event_stream()), headers=headers)

@notification_bp.route('/orders', methods=['POST'])
def publish_order():
    """Publish a message (order) to the single Redis channel.
    Body can be JSON (recommended) or plain text. If empty, a stub with timestamp is published.
    """
    raw_body = request.get_data(as_text=True)
    if raw_body.strip():
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            # Treat as plain text message
            payload = {"text": raw_body}
    else:
        payload = {"info": "empty body", "ts": int(time.time())}

    try:
        redis_client = get_redis()
        # Ensure an order_id if not provided
        if 'order_id' not in payload:
            payload['order_id'] = redis_client.incr('orders:next_id')
        payload.setdefault('created_ts', int(time.time()))
        serialized = json.dumps(payload)
        redis_client.publish(ORDERS_CHANNEL, serialized)
    except redis.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'redis_connection',
            'message': 'Cannot reach Redis at localhost:6379. Start Redis then retry.'
        }), 503

    return jsonify({
        'success': True,
        'published_to': ORDERS_CHANNEL,
        'message': payload
    }), 201

# Optional quick health check
@notification_bp.route('/orders/health')
def orders_health():
    try:
        get_redis().ping()
        return {'status': 'ok', 'channel': ORDERS_CHANNEL}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}, 500