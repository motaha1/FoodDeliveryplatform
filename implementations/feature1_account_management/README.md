# Customer Account Management Feature

## Overview
This implementation uses the **simple request/response pattern** for FoodFast's customer account management system. This pattern is ideal for this feature because:

1. **Immediate confirmation required** - Users need instant feedback for login/registration
2. **Profile updates reflected instantly** - Changes must be visible immediately
3. **Secure operations** - Direct synchronous responses ensure security
4. **Poor internet tolerance** - Simple HTTP requests work better with unreliable connections

## Architecture

### Layered Architecture:
- **Controllers** - Handle HTTP requests/responses
- **Services** - Business logic and validation
- **Models** - Data models and database operations
- **Utils** - Helper functions and utilities
- **Config** - Application configuration

### Security Features:
- JWT token-based authentication
- Password hashing with bcrypt
- Input validation and sanitization
- Secure payment data handling (only last 4 digits stored)

## API Endpoints

### Authentication
- `POST /api/v1/account/register` - Register new account
- `POST /api/v1/account/login` - User login

### Profile Management
- `GET /api/v1/account/profile` - Get user profile
- `PUT /api/v1/account/profile` - Update profile

### Payment Methods
- `POST /api/v1/account/payment-methods` - Add payment method
- `GET /api/v1/account/payment-methods` - Get payment methods
- `DELETE /api/v1/account/payment-methods/{id}` - Delete payment method
- `PUT /api/v1/account/payment-methods/{id}/default` - Set default payment method

### Health Check
- `GET /api/v1/account/health` - Service health check

## Request/Response Examples

### Registration
```json
POST /api/v1/account/register
{
  "email": "customer@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}

Response:
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user": {...},
    "access_token": "...",
    "refresh_token": "..."
  }
}
```

### Login
```json
POST /api/v1/account/login
{
  "email": "customer@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {...},
    "access_token": "...",
    "refresh_token": "..."
  }
}
```

## Security Considerations

1. **Password Security**: 
   - Minimum 8 characters
   - Must contain uppercase, lowercase, digit, and special character
   - Hashed with bcrypt

2. **Payment Security**:
   - Only last 4 digits stored
   - No CVV or full card numbers in database
   - Card validation using Luhn algorithm

3. **Token Security**:
   - JWT tokens with expiration
   - Access tokens expire in 1 hour
   - Refresh tokens expire in 30 days

## Installation and Usage

1. Install dependencies:
   ```bash
   pip install flask flask-jwt-extended flask-sqlalchemy flask-bcrypt marshmallow python-dotenv
   ```

2. Set environment variables:
   ```bash
   export JWT_SECRET_KEY="your-secure-secret-key"
   export DATABASE_URL="sqlite:///foodfast_accounts.db"
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## Why Simple Request/Response Pattern?

This pattern is perfect for account management because:

1. **Synchronous Operations**: Account operations need immediate confirmation
2. **Data Consistency**: Profile updates must be consistent and immediate
3. **Security**: Direct responses ensure secure token exchange
4. **Simplicity**: Easy to debug and maintain
5. **Reliability**: Works well with poor internet connections
6. **Performance**: Low latency for critical user operations

The simple request/response pattern ensures that users get immediate feedback for all account operations, which is crucial for a good user experience in account management scenarios.
