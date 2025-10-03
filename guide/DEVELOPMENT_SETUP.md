# Development Setup Guide

This guide helps you set up the NAL-Backend for development.

## 🚀 Quick Start (Without Database)

If you want to test the application without setting up a database:

```bash
cd /Users/akseth/Alstonair/Code_Workspace/NAL-BACKEND
poetry run python -m src
```

The application will start and handle database connection gracefully in development mode.

## 🗄️ Full Setup with Database

### 1. Install PostgreSQL

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows
Download and install from [PostgreSQL Official Website](https://www.postgresql.org/download/windows/)

### 2. Create Database User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create user and database
CREATE USER postgres WITH PASSWORD 'password';
CREATE DATABASE alstonair_db OWNER postgres;
GRANT ALL PRIVILEGES ON DATABASE alstonair_db TO postgres;
\q
```

### 3. Set Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_POSTGRES_DB_HOST=localhost
DB_POSTGRES_DB_PORT=5432
DB_POSTGRES_DB_NAME=alstonair_db
DB_POSTGRES_DB_USERNAME=postgres
DB_POSTGRES_DB_PASSWORD=password

# Application Settings
APP_ENVIRONMENT=dev
APP_LOG_LEVEL=DEBUG

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Redis Configuration (Optional for development)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Run Database Setup

```bash
cd /Users/akseth/Alstonair/Code_Workspace/NAL-BACKEND
poetry run python setup_database.py
```

### 5. Start the Application

```bash
poetry run python -m src
```

## 🧪 Testing the API

Once the server is running, you can test the endpoints:

### Health Check
```bash
curl http://localhost:8090/api/azure/health
```

### Send OTP (Mock Mode)
```bash
curl -X POST "http://localhost:8090/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'
```

Check the server logs for the OTP code.

### Login
```bash
curl -X POST "http://localhost:8090/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "otp_code": "123456"}'
```

### Complete Profile
```bash
curl -X POST "http://localhost:8090/api/profile/complete" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_data": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com"
    }
  }'
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8090/api/docs
- **ReDoc**: http://localhost:8090/api/redoc

## 🔧 Development Tools

### Install Dependencies
```bash
poetry install
```

### Run Tests
```bash
poetry run pytest
```

### Code Formatting
```bash
poetry run black src/
poetry run isort src/
```

### Type Checking
```bash
poetry run mypy src/
```

## 🐛 Troubleshooting

### Database Connection Issues

1. **Check PostgreSQL Status**
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Ubuntu
   sudo systemctl status postgresql
   ```

2. **Check Database Exists**
   ```bash
   psql -h localhost -U postgres -l
   ```

3. **Reset Database**
   ```bash
   dropdb -h localhost -U postgres alstonair_db
   createdb -h localhost -U postgres alstonair_db
   ```

### Port Already in Use

If port 8090 is already in use:
```bash
# Find process using port 8090
lsof -i :8090

# Kill the process
kill -9 <PID>
```

### Environment Variables Not Loading

Make sure your `.env` file is in the project root and has the correct format:
```env
DB_POSTGRES_DB_HOST=localhost
DB_POSTGRES_DB_PORT=5432
```

## 🚀 Production Deployment

For production deployment:

1. Set `APP_ENVIRONMENT=production`
2. Use strong JWT secrets
3. Configure proper database credentials
4. Set up Redis for caching
5. Configure SMS service (Twilio/AWS SNS)
6. Set up monitoring and logging

## 📞 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Ensure PostgreSQL is running
4. Check network connectivity
5. Review the API documentation at `/api/docs`

