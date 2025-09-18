import redis
from typing import Optional
from config.settings import Config


_redis: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        params = dict(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
            ssl=True,                # Azure requires TLS
            ssl_cert_reqs=None       # Skip local cert verification
        )
        if Config.REDIS_PASSWORD:
            params['username'] = "default"   # ✅ Required for Azure
            params['password'] = Config.REDIS_PASSWORD
        _redis = redis.Redis(**params)
    return _redis

def get_pubsub():
    return get_redis().pubsub()

def main():
    r = get_redis()

    # Test ping
    print("PING:", r.ping())

    # Test set/get
    r.set("test-key", "hello azure redis")
    print("GET test-key:", r.get("test-key"))

    # Pub/Sub test
    pubsub = get_pubsub()
    pubsub.subscribe("test-channel")
    print("Subscribed to 'test-channel'")

    # Publish a message
    r.publish("test-channel", "hello from publisher")

    # Try to read one message
    message = pubsub.get_message(timeout=2)
    if message:
        print("PubSub received:", message)
    else:
        print("No pubsub message received")

if __name__ == "__main__":
    main()
