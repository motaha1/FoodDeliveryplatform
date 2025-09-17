from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.user_service import UserService, PaymentService
from ..utils.auth_helpers import JWTManager  # added import
import logging

logger = logging.getLogger(__name__)

# Create Blueprint for account management
account_bp = Blueprint('account', __name__, url_prefix='/api/v1/account')

# Simple response helpers (local)

def ok(data=None, message="Success", status=200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status

def err(message="Error", errors=None, status=400):
    body = {"success": False, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status

@account_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        result = UserService.register_user(data)

        if result['success']:
            return ok({
                'user': result['user'],
                'access_token': result['tokens']['access_token'],
                'refresh_token': result['tokens']['refresh_token']
            }, "Account created successfully", 201)
        return err("Validation failed", result.get('errors'), 422)

    except Exception as e:
        logger.error(f"Registration endpoint error: {e}")
        return err("Registration failed", status=500)

@account_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        result = UserService.authenticate_user(data)

        if result['success']:
            return ok({
                'user': result['user'],
                'access_token': result['tokens']['access_token'],
                'refresh_token': result['tokens']['refresh_token']
            }, "Login successful")
        return err("Authentication failed", result.get('errors'), 401)

    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        return err("Login failed", status=500)

@account_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        result = UserService.get_user_profile(user_id)

        if result['success']:
            return ok({'user': result['user']}, "Profile retrieved successfully")
        return err("Failed to retrieve profile", result.get('errors'), 404)

    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return err("Failed to retrieve profile", status=500)

@account_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        result = UserService.update_user_profile(user_id, data)

        if result['success']:
            return ok({'user': result['user']}, "Profile updated successfully")
        return err("Validation failed", result.get('errors'), 422)

    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return err("Profile update failed", status=500)

@account_bp.route('/payment-methods', methods=['POST'])
@jwt_required()
def add_payment_method():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        result = PaymentService.add_payment_method(user_id, data)

        if result['success']:
            return ok({'payment_method': result['payment_method']}, "Payment method added successfully", 201)
        return err("Validation failed", result.get('errors'), 422)

    except Exception as e:
        logger.error(f"Add payment method error: {e}")
        return err("Failed to add payment method", status=500)

@account_bp.route('/payment-methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    try:
        user_id = get_jwt_identity()
        result = PaymentService.get_payment_methods(user_id)

        if result['success']:
            return ok({'payment_methods': result['payment_methods']}, "Payment methods retrieved successfully")
        return err("Failed to retrieve payment methods", result.get('errors'), 404)

    except Exception as e:
        logger.error(f"Get payment methods error: {e}")
        return err("Failed to retrieve payment methods", status=500)

@account_bp.route('/payment-methods/<int:payment_method_id>', methods=['DELETE'])
@jwt_required()
def delete_payment_method(payment_method_id):
    try:
        user_id = get_jwt_identity()
        result = PaymentService.delete_payment_method(user_id, payment_method_id)

        if result['success']:
            return ok(message="Payment method deleted successfully")
        return err("Failed to delete payment method", result.get('errors'), 404)

    except Exception as e:
        logger.error(f"Delete payment method error: {e}")
        return err("Failed to delete payment method", status=500)

@account_bp.route('/payment-methods/<int:payment_method_id>/default', methods=['PUT'])
@jwt_required()
def set_default_payment_method(payment_method_id):
    try:
        user_id = get_jwt_identity()
        result = PaymentService.set_default_payment_method(user_id, payment_method_id)

        if result['success']:
            return ok(message="Default payment method updated successfully")
        return err("Failed to set default payment method", result.get('errors'), 404)

    except Exception as e:
        logger.error(f"Set default payment method error: {e}")
        return err("Failed to set default payment method", status=500)

@account_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    try:
        user_id = get_jwt_identity()
        new_access = JWTManager.refresh_access_token(user_id)
        return ok({'access_token': new_access}, "Token refreshed")
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        return err("Failed to refresh token", status=500)
