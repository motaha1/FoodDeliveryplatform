from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from implementations.extensions import db
except ImportError:
    # Fallback if extensions not available
    db = SQLAlchemy()

class Announcement(db.Model):
    """Model for storing employee announcements."""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender_name = db.Column(db.String(100), nullable=False, default='Admin')
    priority = db.Column(db.String(20), nullable=False, default='normal')  # low, normal, high, urgent
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    def to_dict(self):
        """Convert announcement to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'sender_name': self.sender_name,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<Announcement {self.id}: {self.title}>'