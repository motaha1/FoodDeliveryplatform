from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
import time
import threading
from typing import Dict, List, Optional
from queue import Queue
from config.settings import Config
from implementations.feature6_announcements.models.announcement import Announcement, db

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

# Redis client using central Config (points to Azure by default)
redis_client = None
if redis is not None:
    try:
        redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            password=Config.REDIS_PASSWORD or None,
            db=Config.REDIS_DB,
            decode_responses=True,
            ssl=True,               # Azure uses TLS
            ssl_cert_reqs=None      # relax cert verification for local/dev
        )
    except Exception:
        redis_client = None

CHANNEL = "announcements"

class AnnouncementStreamManager:
    """Simple manager for SSE client queues for announcements."""
    def __init__(self):
        self.active_streams: List[Queue] = []
        self.lock = threading.Lock()

    def register_client(self) -> Queue:
        """Register a new SSE client."""
        q = Queue(maxsize=50)
        with self.lock:
            self.active_streams.append(q)
        return q

    def unregister_client(self, q: Queue):
        """Unregister an SSE client."""
        with self.lock:
            try:
                self.active_streams.remove(q)
            except ValueError:
                pass

    def broadcast_announcement(self, announcement_data: dict):
        """Send announcement to all connected clients."""
        data = json.dumps(announcement_data)
        with self.lock:
            alive = []
            for q in self.active_streams:
                try:
                    q.put_nowait(data)
                    alive.append(q)
                except Exception:
                    # Queue full or client disconnected
                    pass
            self.active_streams = alive

# Global stream manager
stream_manager = AnnouncementStreamManager()

announcement_bp = Blueprint('announcements', __name__, url_prefix='/api/v1/announcements')

def _cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

@announcement_bp.route('', methods=['OPTIONS'])
def announcements_options():
    """CORS preflight."""
    return _cors_headers(Response(status=204))

@announcement_bp.route('', methods=['POST'])
def create_announcement():
    """Create a new announcement and broadcast it."""
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()
    sender_name = data.get('sender_name', 'Admin').strip()
    priority = data.get('priority', 'normal').strip()
    
    # Validation
    if not title:
        return _cors_headers(jsonify({'success': False, 'error': 'Title is required'})), 400
    
    if not message:
        return _cors_headers(jsonify({'success': False, 'error': 'Message is required'})), 400
    
    if priority not in ['low', 'normal', 'high', 'urgent']:
        priority = 'normal'
    
    try:
        # Save to database
        announcement = Announcement(
            title=title,
            message=message,
            sender_name=sender_name,
            priority=priority
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        # Prepare announcement data
        announcement_data = announcement.to_dict()
        
        # Broadcast via Redis if available
        if redis_client is not None:
            try:
                event = {
                    "announcement": announcement_data,
                    "ts": int(time.time()),
                }
                redis_client.publish(CHANNEL, json.dumps(event))
            except Exception:
                pass  # Continue even if Redis fails
        
        # Broadcast to local SSE clients
        stream_manager.broadcast_announcement(announcement_data)
        
        return _cors_headers(jsonify({'success': True, 'announcement': announcement_data})), 201
        
    except Exception as e:
        db.session.rollback()
        return _cors_headers(jsonify({'success': False, 'error': str(e)})), 400

@announcement_bp.route('', methods=['GET'])
def get_announcements():
    """Get recent announcements."""
    limit = request.args.get('limit', 10, type=int)
    try:
        announcements = Announcement.query.filter_by(is_active=True)\
                                       .order_by(Announcement.created_at.desc())\
                                       .limit(limit).all()
        announcement_list = [ann.to_dict() for ann in announcements]
        return _cors_headers(jsonify({'success': True, 'announcements': announcement_list}))
    except Exception:
        return _cors_headers(jsonify({'success': True, 'announcements': []}))

@announcement_bp.route('/stream', methods=['GET'])
def stream_announcements():
    """Stream announcements using SSE for real-time notifications."""
    
    def event_stream():
        # Try Redis first
        if redis_client is not None:
            try:
                pubsub = redis_client.pubsub()
                pubsub.subscribe(CHANNEL)
                
                # Let client know stream is alive
                yield "event: ping\ndata: connected\n\n"
                
                # Send recent announcements first
                try:
                    recent = Announcement.query.filter_by(is_active=True)\
                                           .order_by(Announcement.created_at.desc())\
                                           .limit(5).all()
                    for announcement in recent:
                        yield f"data: {json.dumps(announcement.to_dict())}\n\n"
                except Exception:
                    pass
                
                # Listen for new announcements via Redis
                for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    data = message.get("data")
                    yield f"data: {data}\n\n"
                return
                
            except Exception:
                # Fall back to local streaming
                pass
        
        # Fallback: Local SSE streaming
        client_queue = stream_manager.register_client()
        
        try:
            # Send recent announcements first
            try:
                recent = Announcement.query.filter_by(is_active=True)\
                                       .order_by(Announcement.created_at.desc())\
                                       .limit(5).all()
                for announcement in recent:
                    yield f"data: {json.dumps(announcement.to_dict())}\n\n"
            except Exception:
                pass
            
            # Send a connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to announcements'})}\n\n"
            
            # Listen for new announcements
            while True:
                try:
                    # Wait for new announcement or timeout for keepalive
                    data = client_queue.get(timeout=30)
                    yield f"data: {data}\n\n"
                except:
                    # Timeout - send keepalive
                    yield ": keepalive\n\n"
                    
        except GeneratorExit:
            # Client disconnected
            stream_manager.unregister_client(client_queue)
            return
        finally:
            # Cleanup
            stream_manager.unregister_client(client_queue)

    resp = Response(stream_with_context(event_stream()), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Connection"] = "keep-alive"
    return _cors_headers(resp)