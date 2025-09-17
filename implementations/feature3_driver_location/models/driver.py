from datetime import datetime
from implementations.extensions import db

class DriverLocation(db.Model):
    __tablename__ = 'driver_locations'

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, nullable=False, index=True)
    order_id = db.Column(db.Integer, nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'order_id': self.order_id,
            'latitude': round(self.latitude, 6),
            'longitude': round(self.longitude, 6)
        }

class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_online = db.Column(db.Boolean, default=False)
    current_order_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_online': self.is_online,
            'current_order_id': self.current_order_id
        }
