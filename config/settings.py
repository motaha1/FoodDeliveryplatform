import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env so os.environ has values when running locally
load_dotenv()
class Config:
    # Core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_HOURS')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_DAYS')))
    JWT_HEADER_TYPE = 'Bearer'

    # Database (single unified database for all features)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, 'instance', 'foodplateformdb.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', '4'))

    # Orders
    LONG_POLL_TIMEOUT = int(os.environ.get('LONG_POLL_TIMEOUT', '30'))
    ORDER_STATUSES = ['confirmed','preparing','ready','picked_up','delivered','cancelled']

    # Redis - Azure Redis Configuration
    REDIS_HOST = os.environ.get('REDIS_HOST')
    REDIS_PORT = int(os.environ.get('REDIS_PORT'))
    REDIS_DB = int(os.environ.get('REDIS_DB'))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
