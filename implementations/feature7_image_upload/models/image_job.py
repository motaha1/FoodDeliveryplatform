from datetime import datetime
from implementations.extensions import db

class ImageJob(db.Model):
    __tablename__ = 'image_jobs'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='pending')  # pending, processing, completed, failed
    error = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'job_id': self.id,
            'filename': self.filename,
            'status': self.status,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

