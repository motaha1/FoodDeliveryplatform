from datetime import datetime
from implementations.extensions import db
from implementations.feature1_account_management.models.user import User

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.Integer, primary_key=True)
    customer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relationship
    customer = db.relationship(User, lazy='joined')
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_user_id': self.customer_user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'customer': self.customer.email if self.customer else None
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'customer' or 'agent'
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    sender = db.relationship(User, lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'sender_user_id': self.sender_user_id,
            'sender': (self.sender.email.split('@')[0] if self.sender else None),
            'role': self.role,
            'text': self.text,
            'ts': self.created_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }

