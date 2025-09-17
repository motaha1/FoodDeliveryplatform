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
            ssl=True,  # Azure Redis requires SSL
            ssl_cert_reqs=None  # Disable SSL certificate verification for Azure Redis
        )
        if Config.REDIS_PASSWORD:
            params['password'] = Config.REDIS_PASSWORD
        _redis = redis.Redis(**params)
    return _redis

def get_pubsub():
    return get_redis().pubsub()
