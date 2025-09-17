from datetime import datetime, timedelta
from typing import Optional, List
from ..models.order import Order, db
import json

class OrderService:
    def create_sample_orders(self):
        if Order.query.first():
            return "Sample orders already exist"
        samples = [
            {'customer_id': 1,'status': 'confirmed','delivery_address': 'Addr 1','items': ['Item A'],'total_amount': 10.0},
            {'customer_id': 1,'status': 'preparing','delivery_address': 'Addr 2','items': ['Item B'],'total_amount': 20.0},
        ]
        for s in samples:
            o = Order(
                customer_id=s['customer_id'],
                status=s['status'],
                delivery_address=s['delivery_address'],
                items=json.dumps(s['items']),
                total_amount=s['total_amount']
            )
            db.session.add(o)
        db.session.commit()
        return "Seeded"

    def get_order(self, order_id: int) -> Optional[Order]:
        return Order.query.get(order_id)

    def get_customer_orders(self, customer_id: int) -> List[Order]:
        return Order.query.filter_by(customer_id=customer_id).all()

    def get_all_orders(self) -> List[Order]:
        """Get all orders for employee dashboard, ordered by creation date"""
        return Order.query.order_by(Order.created_at.desc()).all()

    def update_order_status(self, order_id: int, new_status: str) -> bool:
        o = Order.query.get(order_id)
        if not o:
            return False
        o.status = new_status
        o.updated_at = datetime.utcnow()
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def create_order(self, customer_id: int, items: list, delivery_address: str, total_amount: float, status: str = 'confirmed', restaurant_name: str | None = None):
        o = Order(
            customer_id=customer_id,
            status=status,
            delivery_address=delivery_address,
            items=json.dumps(items or []),
            total_amount=total_amount,
            restaurant_name=restaurant_name
        )
        db.session.add(o)
        db.session.commit()
        return o

order_service = OrderService()
