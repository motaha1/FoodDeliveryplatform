from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
import re

class JWTManager:
    """JWT token management utilities."""

    @staticmethod
    def generate_tokens(user_id):
        """Generate access and refresh tokens for a user."""
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    @staticmethod
    def refresh_access_token(user_id):
        """Generate a new access token (used with valid refresh token)."""
        return create_access_token(identity=user_id)

    @staticmethod
    def get_current_user_id():
        """Get current user ID from JWT token."""
        return get_jwt_identity()

class ValidationHelper:
    """Validation utilities for account management."""

    @staticmethod
    def validate_registration_data(data):
        """Validate user registration data."""
        errors = []

        # Required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                errors.append(f"{field} is required")

        # Email validation
        if data.get('email') and not ValidationHelper.is_valid_email(data['email']):
            errors.append("Invalid email format")

        # Password validation
        if data.get('password'):
            is_valid, message = ValidationHelper.validate_password_strength(data['password'])
            if not is_valid:
                errors.append(message)

        # Name validation
        if data.get('first_name') and len(data['first_name'].strip()) < 2:
            errors.append("First name must be at least 2 characters")

        if data.get('last_name') and len(data['last_name'].strip()) < 2:
            errors.append("Last name must be at least 2 characters")

        # Role validation
        role = (data.get('role') or '').strip().lower()
        if role and role not in ['customer', 'employee']:
            errors.append("role must be either 'customer' or 'employee'")

        return errors

    @staticmethod
    def validate_login_data(data):
        """Validate user login data."""
        errors = []

        if not data.get('email') or not str(data['email']).strip():
            errors.append("Email is required")

        if not data.get('password') or not str(data['password']).strip():
            errors.append("Password is required")

        return errors

    @staticmethod
    def validate_profile_update_data(data):
        """Validate profile update data."""
        errors = []

        # Optional fields validation
        if data.get('first_name') and len(data['first_name'].strip()) < 2:
            errors.append("First name must be at least 2 characters")

        if data.get('last_name') and len(data['last_name'].strip()) < 2:
            errors.append("Last name must be at least 2 characters")

        return errors

    @staticmethod
    def validate_payment_method_data(data):
        """Validate payment method data."""
        errors = []

        required_fields = ['card_number', 'cardholder_name', 'expiry_month', 'expiry_year', 'cvv']
        for field in required_fields:
            if not data.get(field) or str(data[field]).strip() == '':
                errors.append(f"{field} is required")

        # Card number validation (basic)
        if data.get('card_number') and not ValidationHelper.is_valid_card_number(data['card_number']):
            errors.append("Invalid card number")

        # Expiry validation
        if data.get('expiry_month'):
            try:
                month = int(data['expiry_month'])
                if month < 1 or month > 12:
                    errors.append("Invalid expiry month")
            except ValueError:
                errors.append("Invalid expiry month format")

        if data.get('expiry_year'):
            try:
                year = int(data['expiry_year'])
                if year < 2024 or year > 2040:
                    errors.append("Invalid expiry year")
            except ValueError:
                errors.append("Invalid expiry year format")

        return errors

    @staticmethod
    def is_valid_email(email):
        """Check if email format is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def is_valid_card_number(card_number):
        """Basic card number validation using Luhn algorithm."""
        # Remove spaces and hyphens
        card_number = re.sub(r'[\s-]', '', card_number)

        # Check if all digits
        if not card_number.isdigit():
            return False

        # Check length (13-19 digits for most cards)
        if len(card_number) < 13 or len(card_number) > 19:
            return False

        # Luhn algorithm
        return ValidationHelper._luhn_check(card_number)

    @staticmethod
    def _luhn_check(card_number):
        """Implement Luhn algorithm for card validation."""
        def digits_of(number):
            return [int(d) for d in str(number)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10 == 0

    @staticmethod
    def validate_password_strength(password):
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, "Password is valid"
