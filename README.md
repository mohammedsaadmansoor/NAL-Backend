# NAL-Backend

A FastAPI-based backend service for the NAL Platform, providing AI/ML capabilities, email services, and multi-cloud integrations.

## 🚀 Overview

NAL-Backend is a production-ready microservice built with FastAPI, designed to support AI/ML platform services with comprehensive cloud integrations, database connectivity, and advanced observability features.

## ✨ Features

- **FastAPI Framework** with async/await support
- **Multi-Cloud Integration** (Azure, GCP, Databricks)
- **PostgreSQL Database** with connection pooling
- **Redis Caching** with rate limiting
- **Email Services** with spam prevention
- **Structured Logging** with OpenTelemetry
- **Health Monitoring** endpoints
- **Docker Containerization**
- **Comprehensive Testing** setup

## 🏗️ Architecture

```
src/
├── core/           # Application lifecycle management
├── app/api/        # API routes and endpoints
├── services/       # Business logic services
├── middleware/     # Request/response middleware
├── db/            # Database connections
├── utils/         # Utility functions
└── settings.py    # Configuration management
```

## 🛠️ Technology Stack

- **Python 3.13+**
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **PostgreSQL** - Primary database
- **Redis** - Caching and rate limiting
- **Poetry** - Dependency management
- **Docker** - Containerization
- **Loguru** - Advanced logging
- **OpenTelemetry** - Observability

## 📋 Prerequisites

- Python 3.13 or higher
- Poetry
- Docker (optional)
- PostgreSQL database
- Redis server

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd NAL-BACKEND
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Environment Configuration

Create a `.env` file with the following variables:

```env
# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8090
APP_WORKERS_COUNT=3
APP_RELOAD=true
APP_ENVIRONMENT=NAL-PLATFORM
APP_LOG_LEVEL=DEBUG

# Database Configuration
DB_POSTGRES_DB_HOST=localhost
DB_POSTGRES_DB_PORT=5432
DB_POSTGRES_DB_NAME=nal_db
DB_POSTGRES_DB_USERNAME=postgres
DB_POSTGRES_DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# Email Services
EMAIL_API_ENDPOINT=https://your-email-service.com/api/send
EMAIL_API_ENDPOINT_2=https://your-backup-email-service.com/api/send

# Azure Configuration (Optional)
AZURE_API_KEY=your_azure_key
AZURE_ENDPOINT=https://your-azure-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=your-deployment-name

# GCP Configuration (Optional)
GCP_PROJECT_ID=your-gcp-project
GCP_REGION=us-west1
GCP_BUCKET_NAME=your-bucket
```

### 4. Run the Application

#### Development Mode

```bash
poetry run python -m src
```

#### Production Mode

```bash
poetry run uvicorn src.core.application:get_app --host 0.0.0.0 --port 8090 --workers 3
```

#### Docker

```bash
docker build -t nal-backend .
docker run -p 8090:8000 --env-file .env nal-backend
```

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8090/api/docs`
- **ReDoc**: `http://localhost:8090/api/redoc`
- **OpenAPI JSON**: `http://localhost:8090/api/openapi.json`

## 🔍 Available Endpoints

### Health Check

```http
GET /api/azure/health
```

Returns the health status of the service.

**Response:**
```json
{
  "status": "ok"
}
```

## 🗄️ Database Setup

The application uses PostgreSQL with async connection pooling. Ensure your database is running and accessible with the credentials specified in your environment variables.

### Connection Pool Configuration

- **Min Connections**: 1
- **Max Connections**: 20
- **Connection Timeout**: 30 seconds
- **Command Timeout**: 60 seconds
- **Inactive Connection Lifetime**: 300 seconds

## 📧 Email Service

The email service provides rate-limited email sending with Redis-based counters:

- **Rate Limiting**: 15-minute cooldown periods
- **Dual Endpoints**: Primary and backup email services
- **Counter Management**: Redis-based email tracking
- **Error Handling**: Comprehensive logging and retry logic

## 🔧 Configuration

The application uses a comprehensive settings system with support for multiple cloud providers:

### Supported Services

- **Azure**: OpenAI, Service Bus, Redis Cache
- **Google Cloud**: Vertex AI, Firestore, Cloud Storage
- **Databricks**: ML models and endpoints
- **PostgreSQL**: Primary database
- **Redis**: Caching and rate limiting
- **SMTP**: Email services

### Environment Variables

All configuration is managed through environment variables with appropriate prefixes:

- `APP_*` - Application settings
- `DB_*` - Database configuration
- `REDIS_*` - Redis settings
- `AZURE_*` - Azure services
- `GCP_*` - Google Cloud Platform
- `EMAIL_*` - Email service endpoints

## 🧪 Testing

Run the test suite:

```bash
poetry run pytest
```

The test suite includes:
- Unit tests for services
- Integration tests for API endpoints
- Database session management
- FastAPI test client integration

## 📊 Monitoring & Logging

### Logging Features

- **Structured Logging** with Loguru
- **OpenTelemetry Integration** for distributed tracing
- **Request Context Tracking** with conversation/question IDs
- **Custom Formatters** for enhanced log readability

### Health Monitoring

- Built-in health check endpoint
- Database connection monitoring
- Redis connectivity checks
- Service status reporting

## 🚀 Deployment

### Docker Deployment

```bash
# Build the image
docker build -t nal-backend .

# Run with environment file
docker run -p 8090:8000 --env-file .env nal-backend
```

### Production Considerations

- Set `APP_RELOAD=false` in production
- Configure appropriate `APP_WORKERS_COUNT`
- Use environment-specific logging levels
- Ensure proper database connection pooling
- Configure Redis for high availability

## 🔒 Security

- Non-root Docker user
- Environment variable-based secrets management
- Request validation with Pydantic
- Exception handling with sanitized error messages
- Rate limiting for email services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs`
- Review the logs for debugging information

## 🔄 Version History

- **v0.1.0** - Initial release with core functionality
  - FastAPI application setup
  - Database integration
  - Email services
  - Health monitoring
  - Docker support
