from flask import Blueprint, send_from_directory
from flask_socketio import join_room, leave_room, emit
from datetime import datetime
import threading
from implementations.extensions import db
from implementations.feature1_account_management.models.user import User
from implementations.feature5_support_chat.models.chat import ChatSession, ChatMessage

# Create Blueprint for chat functionality
chat_bp = Blueprint('support_chat', __name__, url_prefix='/api/v1/chat')

# Global chat state - moved from feature5 app.py
typing_users = {}  # chat_id -> set of usernames
chat_lock = threading.Lock()

# Utility helper functions (extracted from feature5 app.py)
def _get_or_create_user(username: str, role: str) -> User:
    """Treat provided username as email if contains '@', else build synthetic email."""
    if '@' in username:
        email = username.lower()
    else:
        email = f"{username.lower()}@local.test"
    user = User.query.filter_by(email=email).first()
    if not user:
        # Simple placeholder names
        first = username.split('@')[0][:30] or 'User'
        user = User(email=email, password='Temp1234!!', first_name=first, last_name=role.capitalize())
        db.session.add(user)
        db.session.commit()
    return user

def _chat_history(chat_id: int):
    msgs = (ChatMessage.query
            .filter(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.id.asc())
            .all())
    return [m.to_dict() for m in msgs]

def _session_summary(session: ChatSession):
    last_msg = (ChatMessage.query
                .filter(ChatMessage.chat_id == session.id)
                .order_by(ChatMessage.id.desc())
                .first())
    return {
        'chat_id': session.id,
        'customer': session.customer.email.split('@')[0],
        'created_ts': session.created_at.isoformat(),
        'last_text': last_msg.text if last_msg else '',
        'last_ts': (last_msg.created_at if last_msg else session.created_at).isoformat()
    }

def _list_chats():
    sessions = ChatSession.query.order_by(ChatSession.last_activity_at.desc()).all()
    return [_session_summary(s) for s in sessions]

# HTTP routes for serving chat static files
@chat_bp.route('/client')
def chat_client():
    """Serve the chat client HTML file"""
    return send_from_directory('implementations/feature5_support_chat/static', 'chat_client.html')

# SocketIO event handlers (to be registered with the main app's socketio instance)
def register_chat_socketio_handlers(socketio):
    """Register all chat-related SocketIO event handlers with the main socketio instance"""
    
    @socketio.on('customer_handshake')
    def customer_handshake(data):
        username = (data or {}).get('user') or 'anonymous'
        user = _get_or_create_user(username, 'customer')
        # Single session per customer
        session = ChatSession.query.filter_by(customer_user_id=user.id).first()
        new_chat = False
        if not session:
            session = ChatSession(customer_user_id=user.id)
            db.session.add(session)
            db.session.commit()
            new_chat = True
        join_room(str(session.id))
        history = _chat_history(session.id)
        emit('customer_chat', {
            'chat_id': session.id,
            'history': history,
            'user': username,
            'new_chat': new_chat
        })
        if new_chat:
            emit('new_chat', {
                'chat_id': session.id,
                'customer': username
            }, to='agents')

    @socketio.on('agent_subscribe')
    def agent_subscribe(data):
        join_room('agents')
        emit('chats_list', {'chats': _list_chats()})

    @socketio.on('get_chats')
    def get_chats():
        emit('chats_list', {'chats': _list_chats()})

    @socketio.on('open_chat')
    def open_chat(data):
        cid = (data or {}).get('chat_id')
        if not cid:
            return
        session = ChatSession.query.filter_by(id=cid).first()
        if not session:
            return
        join_room(str(cid))
        emit('chat_opened', {'chat_id': cid, 'history': _chat_history(cid)})

    @socketio.on('send_message')
    def handle_send_message(data):
        cid = data.get('chat_id')
        if not cid:
            return
        text = (data.get('text') or '').strip()
        if not text:
            return
        role = data.get('role', 'customer')
        username = data.get('user', 'anonymous')
        user = _get_or_create_user(username, role)
        session = ChatSession.query.filter_by(id=cid).first()
        if not session:
            return
        msg = ChatMessage(chat_id=session.id, sender_user_id=user.id, role=role, text=text)
        session.last_activity_at = datetime.utcnow()
        db.session.add(msg)
        db.session.commit()
        payload = msg.to_dict()
        emit('message', payload, to=str(session.id))
        emit('delivered', {'chat_id': session.id, 'message_id': payload['id']})

    @socketio.on('typing')
    def handle_typing(data):
        cid = str(data.get('chat_id'))
        if not cid:
            return
        username = data.get('user', 'anonymous')
        is_typing = bool(data.get('is_typing'))
        with chat_lock:
            typing_users.setdefault(cid, set())
            if is_typing:
                typing_users[cid].add(username)
            else:
                typing_users[cid].discard(username)
            others = [u for u in typing_users[cid] if u != username]
        emit('typing_status', {'chat_id': int(cid), 'users': others}, to=cid, include_self=False)

    @socketio.on('connect')
    def on_connect():
        emit('connected', {'message': 'connected'})

    @socketio.on('disconnect')
    def on_disconnect():
        pass