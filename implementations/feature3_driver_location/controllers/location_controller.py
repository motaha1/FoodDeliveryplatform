from flask import Blueprint, request, jsonify, Response, stream_with_context
import json, time
from implementations.feature3_driver_location.services.location_service import location_service
from implementations.feature3_driver_location.models.driver import Driver, db

driver_bp = Blueprint('driver_location', __name__, url_prefix='/api/v1/drivers')

@driver_bp.route('', methods=['POST'])
def create_driver():
    """Create a new driver."""
    data = request.get_json() or {}
    name = data.get('name', 'Driver')
    d = Driver(name=name, is_online=bool(data.get('is_online', True)), current_order_id=data.get('current_order_id'))
    db.session.add(d)
    db.session.commit()
    return jsonify({'success': True, 'driver': d.to_dict()}), 201

@driver_bp.route('/<int:driver_id>/location', methods=['POST'])
def update_driver_location(driver_id):
    """Driver updates their location (minimal: latitude, longitude)."""
    data = request.get_json() or {}

    if 'latitude' not in data or 'longitude' not in data:
        return jsonify({'success': False, 'error': 'latitude_longitude_required'}), 400

    # Fetch or create driver implicitly
    driver = Driver.query.get(driver_id)
    if not driver:
        driver = Driver(id=driver_id, name=f'Driver {driver_id}', is_online=True)
        db.session.add(driver)
        db.session.commit()

    try:
        lat = float(data['latitude'])
        lng = float(data['longitude'])
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'invalid_location_format'}), 400

    # if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
    #     return jsonify({'success': False, 'error': 'invalid_coordinates'}), 400

    # Attach order automatically (from body order_id or default 123) if missing
    if not driver.current_order_id:
        driver.current_order_id = data.get('order_id', 123)
        driver.is_online = True
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    location_data = {'latitude': lat, 'longitude': lng}
    result = location_service.update_driver_location(driver_id, location_data)
    return (jsonify(result), 200) if result.get('success') else (jsonify(result), 400)

@driver_bp.route('/<int:driver_id>/online', methods=['POST'])
def set_driver_online(driver_id):
    """Set driver online/offline and attach current_order_id (minimal)."""
    data = request.get_json() or {}

    driver = Driver.query.get(driver_id)
    if not driver:
        driver = Driver(id=driver_id, name=f'Driver {driver_id}')
        db.session.add(driver)

    if 'is_online' in data:
        driver.is_online = bool(data['is_online'])

    if 'current_order_id' in data:
        driver.current_order_id = data['current_order_id']

    db.session.commit()
    return jsonify({'success': True, 'driver': driver.to_dict()})

# Customer tracking endpoints
customer_bp = Blueprint('customer_tracking', __name__, url_prefix='/api/v1/tracking')

@customer_bp.route('/order/<int:order_id>/location', methods=['GET'])
def get_driver_location(order_id):
    """Return last known location (latitude, longitude)."""
    customer_id = request.args.get('customer_id', type=int)
    if not customer_id:
        return jsonify({'success': False, 'error': 'customer_id_required'}), 400

    location_data = location_service.get_driver_current_location(order_id)
    return (jsonify({'success': True, 'data': location_data}), 200) if location_data else (jsonify({'success': False, 'error': 'no_location_available'}), 404)

@customer_bp.route('/order/<int:order_id>/stream', methods=['GET'])
def stream_driver_location(order_id):
    """Stream driver location using SSE WITHOUT queue/stream_manager.
    Simple polling of DB every 1s; emits only on change + keepalive every 15s."""
    customer_id = request.args.get('customer_id', type=int)
    if not customer_id:
        return jsonify({'success': False, 'error': 'customer_id_required'}), 400

    def event_stream():
        last_payload = None
        last_emit_ts = 0
        last_keepalive = time.time()
        # send current once if exists
        first = location_service.get_driver_current_location(order_id)
        if first:
            last_payload = first
            yield f"data: {json.dumps(first)}\n\n"
            last_emit_ts = time.time()
        try:
            while True:
                time.sleep(1)
                current = location_service.get_driver_current_location(order_id)
                if current and current != last_payload:
                    last_payload = current
                    last_emit_ts = time.time()
                    yield f"data: {json.dumps(current)}\n\n"
                # keepalive every 15s of no data changes
                now = time.time()
                if now - last_keepalive >= 15:
                    last_keepalive = now
                    yield ": keepalive\n\n"
        except GeneratorExit:
            # client disconnected
            return

    return Response(
        stream_with_context(event_stream()),
        headers={
            'Content-Type': 'text/event-stream; charset=utf-8',
            'Cache-Control': 'no-cache, no-transform',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
