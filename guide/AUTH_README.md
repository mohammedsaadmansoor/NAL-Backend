# NAL-Backend Authentication System

A comprehensive, database-driven authentication system for the NAL-Backend API using phone number-based OTP authentication with JWT tokens.

## 🚀 Features

- **Phone Number Authentication**: OTP-based login system
- **JWT Tokens**: Access and refresh token support
- **Database Storage**: All authentication data stored in PostgreSQL
- **Rate Limiting**: Built-in OTP spam protection
- **Token Management**: Secure refresh token storage and revocation
- **User Management**: Complete user lifecycle management
- **Schema Isolation**: All tables in dedicated `nal` schema

## 📊 Database Schema

### Tables in `nal` Schema

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `users` | User accounts | Phone-based authentication, verification status |
| `user_profiles` | Extended user info | Profile completion tracking, preferences |
| `otp_codes` | OTP storage | 5-minute expiry, attempt tracking |
| `rate_limits` | API rate limiting | 15-minute windows, request counting |
| `refresh_tokens` | Token management | Hashed storage, revocation tracking |
| `migrations` | Schema versioning | Migration tracking and history |

## 🔧 API Endpoints

### 1. Send OTP
**POST** `/api/auth/send-otp`

Send a 6-digit OTP to the provided phone number.

**Request:**
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

**Rate Limiting:** 1 request per 15 minutes per phone number

### 2. Verify OTP
**POST** `/api/auth/verify-otp`

Verify the OTP code for a phone number.

**Request:**
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
  "otp_id": 1
}
```

**Attempts:** Maximum 3 attempts per OTP

### 3. Login
**POST** `/api/auth/login`

Complete login flow with OTP verification and token generation.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "uuid-here",
  "phone_number": "+1234567890",
  "is_new_user": true,
  "profile_exists": false,
  "profile_completion_required": true
}
```

### 4. Refresh Token
**POST** `/api/auth/refresh`

Generate new access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "uuid-here",
  "phone_number": "+1234567890",
  "is_new_user": false,
  "profile_exists": false,
  "profile_completion_required": true
}
```

### 5. Logout
**POST** `/api/auth/logout`

Logout user and revoke refresh tokens.

**Option 1: Using Refresh Token (Recommended)**
```bash
curl -X POST "/api/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

**Option 2: Using Access Token**
```bash
curl -X POST "/api/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### 6. Get Profile
**GET** `/api/auth/profile`

Get current user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "uuid-here",
  "phone_number": "+1234567890",
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

## 🔐 Security Features

### Token Management
- **Access Token**: 30 minutes expiry, stateless JWT
- **Refresh Token**: 7 days expiry, stored in database
- **Token Hashing**: Refresh tokens are SHA-256 hashed before storage
- **Revocation**: Proper token revocation on logout

### Rate Limiting
- **OTP Requests**: 1 per 15 minutes per phone number
- **Database Storage**: Rate limits stored in `nal.rate_limits` table
- **Automatic Cleanup**: Old rate limit records cleaned up

### OTP Security
- **Expiry**: 5 minutes from generation
- **Attempts**: Maximum 3 verification attempts
- **Auto-cleanup**: Expired OTPs automatically removed
- **Rate Limiting**: Prevents OTP spam

## 🗄️ Database Functions

### OTP Management
```sql
-- Store OTP code
SELECT store_otp_code('+1234567890', '123456', 5);

-- Verify OTP code
SELECT verify_otp_code('+1234567890', '123456');

-- Clean up expired OTPs
SELECT cleanup_expired_otp_codes();
```

### Rate Limiting
```sql
-- Check rate limit
SELECT check_rate_limit('+1234567890', 'otp', 15, 1);
```

### Refresh Token Management
```sql
-- Store refresh token
SELECT store_refresh_token('user-uuid', 'token-hash', '2024-01-08 00:00:00');

-- Verify refresh token
SELECT verify_refresh_token('token-hash');

-- Revoke user's refresh tokens
SELECT revoke_refresh_token('user-uuid');

-- Revoke specific refresh token
SELECT revoke_specific_refresh_token('token-hash');
```

## 🚀 Quick Start

### 1. Setup Database
```bash
# Run migrations
poetry run python -m src.db.migrate

# Verify tables
PGPASSWORD=postgres psql -h localhost -U postgres -d alstonair_db -c "\dt nal.*"
```

### 2. Start Application
```bash
poetry run python -m src
```

### 3. Test Authentication Flow
```bash
# Send OTP
curl -X POST "http://localhost:8090/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'

# Check OTP in database
PGPASSWORD=postgres psql -h localhost -U postgres -d alstonair_db \
  -c "SELECT otp_code FROM nal.otp_codes WHERE phone_number = '+1234567890' ORDER BY created_at DESC LIMIT 1;"

# Login with OTP
curl -X POST "http://localhost:8090/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "otp_code": "123456"}'

# Use access token for protected endpoints
curl -X GET "http://localhost:8090/api/auth/profile" \
  -H "Authorization: Bearer <access_token>"
```

## 📝 Error Handling

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `RATE_LIMIT_EXCEEDED` | Too many OTP requests | 429 |
| `OTP_EXPIRED` | OTP has expired | 400 |
| `INVALID_OTP` | Wrong OTP code | 400 |
| `MAX_ATTEMPTS_EXCEEDED` | Too many OTP attempts | 400 |
| `TOKEN_EXPIRED` | Access token expired | 401 |
| `INVALID_TOKEN` | Invalid or malformed token | 401 |
| `REFRESH_TOKEN_EXPIRED` | Refresh token expired | 401 |
| `INVALID_REFRESH_TOKEN` | Invalid refresh token | 401 |

### Error Response Format
```json
{
  "detail": {
    "success": false,
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many OTP requests. Please wait before requesting another OTP.",
    "details": {}
  }
}
```

## 🔧 Configuration

### Environment Variables
```env
# Database Configuration
DB_POSTGRES_DB_HOST=localhost
DB_POSTGRES_DB_PORT=5432
DB_POSTGRES_DB_NAME=alstonair_db
DB_POSTGRES_DB_USERNAME=postgres
DB_POSTGRES_DB_PASSWORD=postgres

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
APP_ENVIRONMENT=dev
APP_LOG_LEVEL=DEBUG
APP_HOST=0.0.0.0
APP_PORT=8090
```

## 📊 Monitoring

### Database Queries for Monitoring

```sql
-- Check active OTPs
SELECT phone_number, created_at, expires_at, attempts 
FROM nal.otp_codes 
WHERE is_verified = FALSE AND expires_at > NOW();

-- Check rate limits
SELECT phone_number, request_count, window_start 
FROM nal.rate_limits 
WHERE window_start > NOW() - INTERVAL '1 hour';

-- Check active refresh tokens
SELECT user_id, created_at, expires_at, is_revoked 
FROM nal.refresh_tokens 
WHERE is_revoked = FALSE AND expires_at > NOW();

-- User statistics
SELECT 
  COUNT(*) as total_users,
  COUNT(CASE WHEN is_verified = TRUE THEN 1 END) as verified_users,
  COUNT(CASE WHEN last_login > NOW() - INTERVAL '24 hours' THEN 1 END) as active_24h
FROM nal.users;
```

## 🛠️ Development

### Running Tests
```bash
# Test OTP flow
curl -X POST "http://localhost:8090/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1111111111"}'

# Test rate limiting
curl -X POST "http://localhost:8090/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1111111111"}'
# Should return rate limit error
```

### Database Maintenance
```bash
# Clean up expired data
PGPASSWORD=postgres psql -h localhost -U postgres -d alstonair_db \
  -c "SELECT cleanup_expired_otp_codes();"

PGPASSWORD=postgres psql -h localhost -U postgres -d alstonair_db \
  -c "SELECT cleanup_expired_refresh_tokens();"
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8090/api/docs
- **ReDoc**: http://localhost:8090/api/redoc

## 🔒 Security Best Practices

1. **Change JWT Secret**: Use a strong, unique JWT secret in production
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Rotation**: Implement refresh token rotation for enhanced security
4. **Rate Limiting**: Monitor and adjust rate limits based on usage
5. **Database Security**: Use proper database permissions and connection security
6. **Logging**: Monitor authentication logs for suspicious activity

## 🐛 Troubleshooting

### Common Issues

1. **OTP Not Received**: Check SMS service configuration
2. **Rate Limit Errors**: Wait 15 minutes or check rate limit table
3. **Token Expired**: Use refresh token to get new access token
4. **Database Connection**: Verify PostgreSQL is running and accessible
5. **Migration Errors**: Check migration files and database permissions

### Debug Commands
```bash
# Check application logs
tail -f logs/app.log

# Check database connection
PGPASSWORD=postgres psql -h localhost -U postgres -d alstonair_db -c "SELECT version();"

# Check active processes
ps aux | grep python
```

---

**Note**: This authentication system is designed for development and testing. For production use, implement additional security measures including proper SMS service integration, enhanced rate limiting, and comprehensive monitoring.
