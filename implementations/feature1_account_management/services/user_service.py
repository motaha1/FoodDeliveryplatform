from ..models.user import User, PaymentMethod, db
from ..utils.auth_helpers import JWTManager, ValidationHelper
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service layer for user account management operations."""

    @staticmethod
    def register_user(user_data):
        """Register a new user account."""
        try:
            # Validate input data
            validation_errors = ValidationHelper.validate_registration_data(user_data)
            if validation_errors:
                return {'success': False, 'errors': validation_errors}

            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                return {'success': False, 'errors': ['Email already registered']}

            # Create new user
            user = User(
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data.get('phone'),
                role=(user_data.get('role') or 'customer').strip().lower()
            )

            db.session.add(user)
            db.session.commit()

            # Generate tokens
            tokens = JWTManager.generate_tokens(user.id)

            logger.info(f"User registered successfully: {user.email}")

            return {
                'success': True,
                'user': user.to_dict(),
                'tokens': tokens
            }

        except IntegrityError:
            db.session.rollback()
            return {'success': False, 'errors': ['Email already registered']}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            return {'success': False, 'errors': ['Registration failed. Please try again.']}

    @staticmethod
    def authenticate_user(login_data):
        """Authenticate user login."""
        try:
            # Validate input data
            validation_errors = ValidationHelper.validate_login_data(login_data)
            if validation_errors:
                return {'success': False, 'errors': validation_errors}

            # Find user by email
            user = User.query.filter_by(email=login_data['email'].lower()).first()

            if not user or not user.check_password(login_data['password']):
                return {'success': False, 'errors': ['Invalid email or password']}

            if not user.is_active:
                return {'success': False, 'errors': ['Account is deactivated']}

            # Generate tokens
            tokens = JWTManager.generate_tokens(user.id)

            logger.info(f"User authenticated successfully: {user.email}")

            return {
                'success': True,
                'user': user.to_dict(),
                'tokens': tokens
            }

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'errors': ['Authentication failed. Please try again.']}

    @staticmethod
    def get_user_profile(user_id):
        """Get user profile information."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'errors': ['User not found']}

            return {
                'success': True,
                'user': user.to_dict()
            }

        except Exception as e:
            logger.error(f"Get profile error: {str(e)}")
            return {'success': False, 'errors': ['Failed to retrieve profile']}

    @staticmethod
    def update_user_profile(user_id, update_data):
        """Update user profile information."""
        try:
            # Validate input data
            validation_errors = ValidationHelper.validate_profile_update_data(update_data)
            if validation_errors:
                return {'success': False, 'errors': validation_errors}

            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'errors': ['User not found']}

            # Update allowed fields
            if 'first_name' in update_data and update_data['first_name'].strip():
                user.first_name = update_data['first_name'].strip()

            if 'last_name' in update_data and update_data['last_name'].strip():
                user.last_name = update_data['last_name'].strip()

            if 'phone' in update_data:
                user.phone = update_data['phone'].strip() if update_data['phone'] else None

            db.session.commit()

            logger.info(f"Profile updated for user: {user.email}")

            return {
                'success': True,
                'user': user.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Profile update error: {str(e)}")
            return {'success': False, 'errors': ['Failed to update profile']}

class PaymentService:
    """Service layer for payment method management."""

    @staticmethod
    def add_payment_method(user_id, payment_data):
        """Add a new payment method for user (simplified, no card type detection)."""
        try:
            # Validate input data
            validation_errors = ValidationHelper.validate_payment_method_data(payment_data)
            if validation_errors:
                return {'success': False, 'errors': validation_errors}

            # Verify user exists
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'errors': ['User not found']}

            # Use provided card_type or fallback
            card_type = payment_data.get('card_type', 'unknown')

            # If this is set as default, unset other defaults
            if payment_data.get('is_default', False):
                PaymentMethod.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

            # Create payment method (store only safe data)
            payment_method = PaymentMethod(
                user_id=user_id,
                card_type=card_type,
                last_four=payment_data['card_number'][-4:],
                cardholder_name=payment_data['cardholder_name'].strip(),
                expiry_month=int(payment_data['expiry_month']),
                expiry_year=int(payment_data['expiry_year']),
                is_default=payment_data.get('is_default', False)
            )

            db.session.add(payment_method)
            db.session.commit()

            logger.info(f"Payment method added for user: {user.email}")

            return {
                'success': True,
                'payment_method': payment_method.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Add payment method error: {str(e)}")
            return {'success': False, 'errors': ['Failed to add payment method']}

    @staticmethod
    def get_payment_methods(user_id):
        """Get all payment methods for a user."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'errors': ['User not found']}

            payment_methods = PaymentMethod.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            return {
                'success': True,
                'payment_methods': [pm.to_dict() for pm in payment_methods]
            }

        except Exception as e:
            logger.error(f"Get payment methods error: {str(e)}")
            return {'success': False, 'errors': ['Failed to retrieve payment methods']}

    @staticmethod
    def delete_payment_method(user_id, payment_method_id):
        """Delete a payment method."""
        try:
            payment_method = PaymentMethod.query.filter_by(
                id=payment_method_id,
                user_id=user_id
            ).first()

            if not payment_method:
                return {'success': False, 'errors': ['Payment method not found']}

            payment_method.is_active = False
            db.session.commit()

            logger.info(f"Payment method deleted for user ID: {user_id}")

            return {'success': True}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Delete payment method error: {str(e)}")
            return {'success': False, 'errors': ['Failed to delete payment method']}

    @staticmethod
    def set_default_payment_method(user_id, payment_method_id):
        """Set a payment method as default."""
        try:
            # Unset all defaults for user
            PaymentMethod.query.filter_by(user_id=user_id).update({'is_default': False})

            # Set new default
            payment_method = PaymentMethod.query.filter_by(
                id=payment_method_id,
                user_id=user_id,
                is_active=True
            ).first()

            if not payment_method:
                return {'success': False, 'errors': ['Payment method not found']}

            payment_method.is_default = True
            db.session.commit()

            return {'success': True}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Set default payment method error: {str(e)}")
            return {'success': False, 'errors': ['Failed to set default payment method']}
