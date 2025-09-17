#!/usr/bin/env python3
"""
Full-featured startup script for Azure App Service with SocketIO support
Use this instead of Gunicorn for complete functionality
"""
import sys
import os
import logging

# Configure logging for Azure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    logger.info("Importing Flask app and SocketIO...")
    from app import app, socketio
    
    if __name__ == "__main__":
        # For Azure, get the port from environment
        port = int(os.environ.get('PORT', 8000))
        logger.info(f"Starting SocketIO server on port {port}")
        
        # Run with SocketIO for full functionality (chat, real-time features)
        socketio.run(
            app,
            host='0.0.0.0', 
            port=port, 
            debug=False,
            use_reloader=False,
            log_output=True
        )
        
except Exception as e:
    logger.error(f"Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)