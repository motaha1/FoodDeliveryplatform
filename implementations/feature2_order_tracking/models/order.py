from datetime import datetime
from implementations.extensions import db

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Reintroduce FK to users for unified database
    status = db.Column(db.String(20), nullable=False, default='confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estimated_delivery = db.Column(db.DateTime)
    delivery_address = db.Column(db.Text)
    items = db.Column(db.Text)  # JSON string of items
    total_amount = db.Column(db.Float)
    restaurant_name = db.Column(db.String(100))

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            'delivery_address': self.delivery_address,
            'items': json.loads(self.items) if self.items else [],
            'total_amount': self.total_amount,
            'restaurant_name': self.restaurant_name
        }

    @classmethod
    def from_dict(cls, data):
        import json
        return cls(
            id=data.get('id'),
            customer_id=data.get('customer_id'),
            status=data.get('status'),
            estimated_delivery=datetime.fromisoformat(data.get('estimated_delivery')) if data.get('estimated_delivery') else None,
            delivery_address=data.get('delivery_address'),
            items=json.dumps(data.get('items', [])),
            total_amount=data.get('total_amount'),
            restaurant_name=data.get('restaurant_name')
        )
