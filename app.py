import os
from flask import Flask, send_from_directory, redirect, request
# from flasgger import Swagger  # Temporarily disabled for Azure compatibility
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, join_room, leave_room, emit
from implementations.extensions import db, bcrypt
from config.settings import Config
from implementations.feature1_account_management.controllers.account_controller import account_bp
from implementations.feature2_order_tracking.controllers.order_controller import order_bp
from implementations.feature3_driver_location.controllers.location_controller import driver_bp, customer_bp
from implementations.feature4_restaurant_notifications.controllers.notification_controller import notification_bp
from implementations.feature6_announcements.controllers.announcement_controller import announcement_bp
from implementations.feature5_support_chat.models.chat import ChatSession, ChatMessage
from implementations.feature5_support_chat.controllers.chat_controller import chat_bp, register_chat_socketio_handlers
from implementations.feature1_account_management.models.user import User
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from datetime import datetime
import threading
from implementations.feature7_image_upload.controllers.image_upload_controller import image_upload_bp  # Feature 7 blueprint


def create_app():
  app = Flask(__name__, static_folder='static')

  # Central config
  app.config.from_object(Config)

  # Ensure instance directory exists
  instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
  os.makedirs(instance_dir, exist_ok=True)

  # Swagger basic setup - Temporarily disabled for Azure compatibility
  # Swagger(app, template={
  #   "swagger": "2.0",
  #   "info": {"title": "FoodFast API", "version": "1.0.0"},
  #   "securityDefinitions": {
  #     "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
  #   }
  # })

  # Extensions
  db.init_app(app)
  bcrypt.init_app(app)
  jwt = JWTManager(app)
  
  # JWT error handlers
  @jwt.expired_token_loader
  def expired_token_callback(jwt_header, jwt_payload):
    return {'success': False, 'message': 'Token has expired', 'error': 'token_expired'}, 401

  @jwt.invalid_token_loader
  def invalid_token_callback(error):
    return {'success': False, 'message': 'Invalid token', 'error': 'token_invalid'}, 422

  @jwt.unauthorized_loader
  def missing_token_callback(error):
    return {'success': False, 'message': 'Authorization token is required', 'error': 'token_missing'}, 401
  
  # Useful middleware from feature1
  @app.before_request
  def normalize_auth_header():
    """Normalize Authorization header: if user supplies only the raw JWT (no 'Bearer '), prepend it"""
    auth = request.headers.get('Authorization')
    if auth and not auth.startswith('Bearer '):
      # Heuristic: JWT normally has 2 dots
      if auth.count('.') == 2:
        # Inject modified header into environ so flask_jwt_extended sees it
        request.environ['HTTP_AUTHORIZATION'] = f'Bearer {auth}'

  @app.before_request
  def validate_json():
    """Request validation middleware for JSON content type"""
    if request.method in ['POST', 'PUT', 'PATCH']:
      if request.content_type and 'application/json' not in request.content_type:
        return {
          'success': False,
          'message': 'Content-Type must be application/json'
        }, 400
  
  # Initialize SocketIO for chat support
  socketio = SocketIO(app, cors_allowed_origins='*')

  # Blueprints (one modular monolith)
  app.register_blueprint(account_bp)
  app.register_blueprint(order_bp)
  app.register_blueprint(driver_bp)
  app.register_blueprint(customer_bp)
  app.register_blueprint(notification_bp)
  app.register_blueprint(announcement_bp)
  app.register_blueprint(chat_bp)  # Feature 5 chat controller
  app.register_blueprint(image_upload_bp)  # register Feature 7

  # Create all tables
  with app.app_context():
    try:
      db.create_all()
      inspector = inspect(db.engine)
      print('[App] Tables:', inspector.get_table_names())
      # Lightweight migration: ensure 'role' column exists on users
      if 'users' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('users')]
        if 'role' not in cols:
          try:
            with db.engine.connect() as conn:
              conn.execute(db.text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'customer';"))
            print("[App] Added 'role' column to users table")
          except OperationalError as e:
            print('[App] Migration failed (role):', e)
    except Exception as e:
      print('[App] Database error:', e)

  # Static templates serving
  @app.route('/')
  def root():
    return redirect('/templates/index.html')

  @app.route('/templates/<path:filename>')
  def templates_file(filename):
    return send_from_directory('templates', filename)

  @app.route('/debug/tables', methods=['GET'])
  def debug_tables():
    """Debug endpoint to show database tables"""
    try:
      inspector = inspect(db.engine)
      return {"tables": inspector.get_table_names()}
    except Exception as e:
      return {"error": str(e)}, 500

  # SocketIO Chat Event Handlers - Register handlers from chat controller
  register_chat_socketio_handlers(socketio)

  return app, socketio


# Create app instance at module level for WSGI (Azure/Gunicorn compatibility)
app, socketio = create_app()

if __name__ == '__main__':
  # Auto-detect environment
  import os
  
  # Check if running on Azure (Azure sets WEBSITE_SITE_NAME)
  is_azure = 'WEBSITE_SITE_NAME' in os.environ
  
  if is_azure:
    # Azure deployment configuration
    port = int(os.environ.get('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
  else:
    # Local development configuration
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
