# Mobile Number Authentication Guide

This guide explains how to use the mobile number-based authentication system in NAL-Backend.

## 🔐 Authentication Flow

The authentication system uses a secure OTP-based flow:

1. **Send OTP** - User provides phone number, system sends OTP via SMS
2. **Verify OTP** - User provides phone number and OTP code for verification
3. **Login** - User completes login with phone number and OTP to get JWT tokens
4. **Access Protected Resources** - Use JWT tokens to access protected endpoints
5. **Refresh Tokens** - Use refresh tokens to get new access tokens
6. **Logout** - Invalidate refresh tokens to log out

## 📱 API Endpoints

### 1. Send OTP

**Endpoint:** `POST /api/auth/send-otp`

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "expires_in": 300,
  "retry_after": 60
}
```

**Rate Limiting:** 1 OTP per phone number per 15 minutes

### 2. Verify OTP

**Endpoint:** `POST /api/auth/verify-otp`

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "phone_number": "+1234567890"
}
```

**Attempts:** Maximum 3 attempts per OTP

### 3. Login

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+1234567890"
}
```

### 4. Refresh Token

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+1234567890"
}
```

### 5. Get Profile

**Endpoint:** `GET /api/auth/profile`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+1234567890",
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z"
}
```

### 6. Logout

**Endpoint:** `POST /api/auth/logout`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# SMS Service Configuration
SMS_PROVIDER=mock  # Options: mock, twilio, aws_sns

# Twilio Configuration (if using Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1234567890

# AWS SNS Configuration (if using AWS SNS)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### SMS Service Setup

#### Mock Service (Development)
```python
from src.services.sms_service import initialize_sms_service

# Initialize mock SMS service
initialize_sms_service("mock")
```

#### Twilio Service (Production)
```python
from src.services.sms_service import initialize_sms_service

# Initialize Twilio SMS service
initialize_sms_service(
    "twilio",
    account_sid="your_account_sid",
    auth_token="your_auth_token",
    from_number="+1234567890"
)
```

#### AWS SNS Service (Production)
```python
from src.services.sms_service import initialize_sms_service

# Initialize AWS SNS service
initialize_sms_service(
    "aws_sns",
    region_name="us-east-1",
    access_key_id="your_access_key",
    secret_access_key="your_secret_key"
)
```

## 🛡️ Security Features

### Rate Limiting
- **OTP Requests:** 1 per phone number per 15 minutes
- **OTP Attempts:** Maximum 3 attempts per OTP
- **Token Refresh:** Rate limited by Redis

### Token Security
- **Access Tokens:** 30 minutes expiry (configurable)
- **Refresh Tokens:** 7 days expiry (configurable)
- **JWT Secret:** Configurable via environment variables
- **Token Storage:** Refresh tokens stored in Redis with expiry

### Phone Number Validation
- **Format Validation:** International format required (+1234567890)
- **Phone Number Library:** Uses `phonenumbers` library for validation
- **Sanitization:** Phone numbers are sanitized before storage

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Migrations Table
```sql
CREATE TABLE migrations (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🧪 Testing

### Manual Testing with cURL

#### 1. Send OTP
```bash
curl -X POST "http://localhost:8090/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'
```

#### 2. Verify OTP
```bash
curl -X POST "http://localhost:8090/api/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "otp_code": "123456"}'
```

#### 3. Login
```bash
curl -X POST "http://localhost:8090/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "otp_code": "123456"}'
```

#### 4. Get Profile
```bash
curl -X GET "http://localhost:8090/api/auth/profile" \
  -H "Authorization: Bearer <access_token>"
```

### Unit Testing

```python
import pytest
from fastapi.testclient import TestClient
from src.core.application import get_app

client = TestClient(get_app())

def test_send_otp():
    response = client.post("/api/auth/send-otp", json={
        "phone_number": "+1234567890"
    })
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_verify_otp():
    # First send OTP
    client.post("/api/auth/send-otp", json={
        "phone_number": "+1234567890"
    })
    
    # Then verify (you'll need to get the actual OTP from logs)
    response = client.post("/api/auth/verify-otp", json={
        "phone_number": "+1234567890",
        "otp_code": "123456"  # Use actual OTP from logs
    })
    assert response.status_code == 200
```

## 🚀 Production Deployment

### 1. Environment Setup
- Set strong JWT secret
- Configure production SMS service
- Set up Redis for token storage
- Configure PostgreSQL database

### 2. Security Considerations
- Use HTTPS in production
- Set strong JWT secrets
- Configure proper CORS settings
- Monitor rate limiting
- Set up logging and monitoring

### 3. SMS Service Selection
- **Twilio:** Good for global coverage, reliable
- **AWS SNS:** Good for AWS-based infrastructure
- **Mock:** Only for development/testing

### 4. Monitoring
- Monitor OTP send rates
- Track authentication failures
- Monitor token refresh patterns
- Set up alerts for suspicious activity

## 🔍 Troubleshooting

### Common Issues

#### 1. OTP Not Received
- Check SMS service configuration
- Verify phone number format
- Check rate limiting
- Review SMS service logs

#### 2. Token Expired
- Use refresh token to get new access token
- Check token expiry configuration
- Verify system clock synchronization

#### 3. Rate Limit Exceeded
- Wait for cooldown period
- Check Redis configuration
- Review rate limiting settings

#### 4. Database Connection Issues
- Check PostgreSQL connection
- Verify database credentials
- Check connection pool settings

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

This will show:
- OTP codes in logs (development only)
- Detailed error messages
- Request/response details
- Database query logs

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT.io](https://jwt.io/) - JWT token decoder
- [Twilio SMS API](https://www.twilio.com/docs/sms)
- [AWS SNS Documentation](https://docs.aws.amazon.com/sns/)
- [phonenumbers Library](https://github.com/daviddrysdale/python-phonenumbers)
