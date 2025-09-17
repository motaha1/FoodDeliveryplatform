import json
import threading
from typing import Dict, List, Optional
from queue import Queue
from ..models.driver import DriverLocation, Driver, db

class LocationStreamManager:
    """Very simple manager for SSE client queues per order."""
    def __init__(self):
        self.active_streams: Dict[int, List[Queue]] = {}
        self.lock = threading.Lock()

    def register_client(self, order_id: int) -> Queue:
        q = Queue(maxsize=50)
        with self.lock:
            self.active_streams.setdefault(order_id, []).append(q)
        return q

    def unregister_client(self, order_id: int, q: Queue):
        with self.lock:
            if order_id in self.active_streams:
                try:
                    self.active_streams[order_id].remove(q)
                except ValueError:
                    pass
                if not self.active_streams[order_id]:
                    del self.active_streams[order_id]

    def broadcast_location(self, order_id: int, location_obj: dict):
        """Send plain location object (JSON) to all clients."""
        data = json.dumps(location_obj)
        with self.lock:
            queues = self.active_streams.get(order_id) or []
            alive = []
            for q in queues:
                try:
                    q.put_nowait(data)
                    alive.append(q)
                except Exception:
                    pass
            if alive:
                self.active_streams[order_id] = alive
            elif order_id in self.active_streams:
                del self.active_streams[order_id]

class DriverLocationService:
    """Minimal service: save location and stream it to clients as a simple object."""
    def __init__(self):
        self.stream_manager = LocationStreamManager()

    def update_driver_location(self, driver_id: int, location_data: dict) -> dict:
        driver = Driver.query.get(driver_id)
        if not driver:
            return {'success': False, 'error': 'driver_not_found'}
        if not driver.current_order_id:
            return {'success': False, 'error': 'no_active_delivery'}

        loc = DriverLocation(
            driver_id=driver_id,
            order_id=driver.current_order_id,
            latitude=float(location_data['latitude']),
            longitude=float(location_data['longitude'])
        )
        try:
            db.session.add(loc)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

        payload = {
            'latitude': loc.latitude,
            'longitude': loc.longitude
        }
        self.stream_manager.broadcast_location(driver.current_order_id, payload)
        return {'success': True, 'location': payload}

    def get_location_stream(self, order_id: int, customer_id: int) -> Queue:
        """Minimal access control: separate DB, no cross-feature validation."""
        return self.stream_manager.register_client(order_id)

    def get_driver_current_location(self, order_id: int) -> Optional[dict]:
        last = (DriverLocation.query
                .filter_by(order_id=order_id)
                .order_by(DriverLocation.id.desc())
                .first())
        if not last:
            return None
        return {
            'latitude': last.latitude,
            'longitude': last.longitude
        }

# Global service instance
location_service = DriverLocationService()
