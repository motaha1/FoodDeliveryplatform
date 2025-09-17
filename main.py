#!/usr/bin/env python3
"""
WSGI entry point for Azure App Service - Gunicorn compatible
"""
import os
import sys
import logging

# Configure logging for Azure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    logger.info("Starting application import...")
    
    # Import the pre-created app instance from app.py
    from app import app, socketio
    
    logger.info("App imported successfully!")
    
    # For Gunicorn, we need to expose the Flask app directly (not SocketIO)
    # SocketIO functionality will be limited in Gunicorn, but basic Flask routes will work
    application = app
    
except Exception as e:
    logger.error(f"Failed to import application: {e}")
    import traceback
    logger.error(traceback.format_exc())
    
    # Create a minimal fallback app
    from flask import Flask, jsonify
    application = Flask(__name__)
    
    @application.route('/')
    def hello():
        return '<h1>Food Delivery Platform</h1><p>App is running! (Limited mode - SocketIO features may not work with Gunicorn)</p>'
    
    @application.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'App is running'})

if __name__ == "__main__":
    # This won't be called when using Gunicorn, but useful for direct execution
    try:
        port = int(os.environ.get('PORT', 8000))
        logger.info(f"Running on port {port}")
        application.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to run application: {e}")
        sys.exit(1)