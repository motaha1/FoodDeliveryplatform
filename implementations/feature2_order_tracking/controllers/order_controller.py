from flask import Blueprint, request, jsonify
from datetime import datetime
import time
import json
from implementations.feature2_order_tracking.services.order_service import order_service
from implementations.feature1_account_management.models.user import User
from implementations.feature4_restaurant_notifications.services.redis_client import get_redis
import redis.exceptions

order_bp = Blueprint('order_tracking', __name__, url_prefix='/api/v1/orders')

@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = order_service.get_order(order_id)
    if not order:
        return jsonify({'success': False, 'error': 'order_not_found'}), 404
    return jsonify({'success': True, 'data': order.to_dict()})

@order_bp.route('/<int:order_id>/track', methods=['GET'])
def track_order_long_polling(order_id):
    last_status = request.args.get('last_status')
    timeout = int(request.args.get('timeout', 30))
    if timeout > 60:
        timeout = 60

    order = order_service.get_order(order_id)
    if not order:
        return jsonify({'success': False, 'error': 'order_not_found'}), 404

    # If client has no last_status -> immediate return (treat as update)
    if last_status is None:
        return jsonify({'success': True, 'data': order.to_dict(), 'has_update': True})

    # If order is ready and client does not yet have that status -> immediate
    if order.status == 'ready' and last_status != 'ready':
        return jsonify({'success': True, 'data': order.to_dict(), 'has_update': True})

    # If status already different right away
    if order.status != last_status:
        return jsonify({'success': True, 'data': order.to_dict(), 'has_update': True})

    # Poll until status changes or timeout
    start = time.time()
    interval = 2
    while time.time() - start < timeout:
        current = order_service.get_order(order_id)
        if not current:
            return jsonify({'success': False, 'error': 'order_not_found'}), 404
        if current.status != last_status:
            return jsonify({'success': True, 'data': current.to_dict(), 'has_update': True})
        time.sleep(interval)

    # Timeout without change
    current = order_service.get_order(order_id)
    if not current:
        return jsonify({'success': False, 'error': 'order_not_found'}), 404
    return jsonify({'success': True, 'data': current.to_dict(), 'has_update': False})

@order_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_customer_orders(customer_id):
    orders = order_service.get_customer_orders(customer_id)
    return jsonify({'success': True, 'data': [o.to_dict() for o in orders]})

@order_bp.route('/all', methods=['GET'])
def get_all_orders():
    orders = order_service.get_all_orders()
    return jsonify({'success': True, 'data': [o.to_dict() for o in orders]})

@order_bp.route('/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json(silent=True) or {}
    status = data.get('status')
    valid = ['confirmed','preparing','ready','picked_up','delivered','cancelled']
    if status not in valid:
        return jsonify({'success': False, 'error': 'invalid_status', 'valid': valid}), 400
    if not order_service.update_order_status(order_id, status):
        return jsonify({'success': False, 'error': 'order_not_found'}), 404
    order = order_service.get_order(order_id)
    return jsonify({'success': True, 'data': order.to_dict()})

@order_bp.route('', methods=['POST'])
@order_bp.route('/', methods=['POST'])
def create_order():
    data = request.get_json(silent=True) or {}
    required = ['customer_id', 'items', 'delivery_address', 'total_amount']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'success': False, 'error': 'missing_fields', 'fields': missing}), 400
    # Basic type validations
    if not isinstance(data.get('items'), list):
        return jsonify({'success': False, 'error': 'items_must_be_list'}), 400
    try:
        customer_id = int(data['customer_id'])
    except Exception:
        return jsonify({'success': False, 'error': 'invalid_customer_id'}), 400
    # Ensure customer exists to avoid FK error that looks like 500 to Swagger
    if not User.query.get(customer_id):
        return jsonify({'success': False, 'error': 'customer_not_found'}), 404
    status = data.get('status', 'confirmed')
    valid = ['confirmed','preparing','ready','picked_up','delivered','cancelled']
    if status not in valid:
        return jsonify({'success': False, 'error': 'invalid_status', 'valid': valid}), 400
    try:
        order = order_service.create_order(
            customer_id=customer_id,
            items=data['items'],
            delivery_address=str(data['delivery_address']),
            total_amount=float(data['total_amount']),
            status=status,
            restaurant_name=data.get('restaurant_name')
        )
        
        # Send notification via Redis for SSE
        try:
            redis_client = get_redis()
            notification_payload = {
                'order_id': order.id,
                'customer_id': order.customer_id,
                'status': order.status,
                'delivery_address': order.delivery_address,
                'total_amount': order.total_amount,
                'restaurant_name': order.restaurant_name,
                'created_at': order.created_at.isoformat(),
                'items': json.loads(order.items) if order.items else []
            }
            redis_client.publish('orders', json.dumps(notification_payload))
        except redis.exceptions.ConnectionError:
            # Redis is not available, continue without notification
            pass
        except Exception:
            # Other Redis errors, continue without notification
            pass
            
    except Exception as e:
        from sqlalchemy import exc as sa_exc
        if isinstance(e, sa_exc.SQLAlchemyError):
            return jsonify({'success': False, 'error': 'db_error', 'message': str(e.__class__.__name__)}), 400
        return jsonify({'success': False, 'error': 'create_failed', 'message': str(e)}), 400
    return jsonify({'success': True, 'data': order.to_dict()}), 201
