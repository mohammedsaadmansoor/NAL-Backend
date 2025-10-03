# User Profile Management Guide

This guide explains how to use the comprehensive user profile system in NAL-Backend, which automatically integrates with the mobile authentication system.

## 🎯 Overview

The user profile system provides:
- **Automatic Profile Creation** - Profiles are created when users first log in
- **Profile Completion Tracking** - Real-time completion percentage and status
- **Comprehensive User Data** - Personal info, contact details, preferences
- **Search & Discovery** - Find users by name or bio
- **Validation & Security** - Data validation and privacy controls

## 🔄 Profile Completion Flow

### 1. New User Login
When a new user logs in for the first time:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+1234567890",
  "is_new_user": true,
  "profile_exists": false,
  "profile_completion_required": true
}
```

### 2. Profile Completion Required
The client should detect `profile_completion_required: true` and prompt the user to complete their profile.

### 3. Complete Profile
User fills out profile information and submits it.

### 4. Profile Status Updates
The system automatically calculates completion percentage and status.

## 📱 API Endpoints

### 1. Complete User Profile

**Endpoint:** `POST /api/profile/complete`

**Request Body:**
```json
{
  "profile_data": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "date_of_birth": "1990-01-15T00:00:00Z",
    "gender": "male",
    "country": "United States",
    "city": "New York",
    "address": "123 Main St, Apt 4B",
    "postal_code": "10001",
    "profile_picture_url": "https://example.com/profile.jpg",
    "bio": "Software developer passionate about AI and machine learning.",
    "preferences": {
      "notifications": true,
      "theme": "dark",
      "language": "en"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile completed successfully",
  "profile_completion_status": "complete",
  "profile_completion_percentage": 100,
  "missing_fields": []
}
```

### 2. Get My Profile

**Endpoint:** `GET /api/profile/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "date_of_birth": "1990-01-15T00:00:00Z",
  "gender": "male",
  "country": "United States",
  "city": "New York",
  "address": "123 Main St, Apt 4B",
  "postal_code": "10001",
  "profile_picture_url": "https://example.com/profile.jpg",
  "bio": "Software developer passionate about AI and machine learning.",
  "preferences": {
    "notifications": true,
    "theme": "dark",
    "language": "en"
  },
  "profile_completion_status": "complete",
  "profile_completion_percentage": 100,
  "is_verified": true,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "last_login": "2024-01-01T12:00:00Z"
}
```

### 3. Update Profile

**Endpoint:** `PUT /api/profile/me`

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "bio": "Updated bio information",
  "preferences": {
    "notifications": false,
    "theme": "light",
    "language": "es"
  }
}
```

**Response:** Same as GET profile with updated information.

### 4. Get Profile Completion Status

**Endpoint:** `GET /api/profile/completion-status`

**Response:**
```json
{
  "completion_status": "basic",
  "completion_percentage": 60,
  "missing_required_fields": [],
  "missing_basic_fields": ["email", "date_of_birth"],
  "missing_location_fields": ["country"],
  "missing_additional_fields": ["bio", "profile_picture_url"]
}
```

### 5. Search Users

**Endpoint:** `GET /api/profile/search?query=john&limit=10&offset=0`

**Response:**
```json
{
  "users": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "phone_number": "+1234567890",
      "first_name": "John",
      "last_name": "Doe",
      "profile_completion_status": "complete",
      "profile_completion_percentage": 100,
      "is_verified": true,
      "status": "active"
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

### 6. Get Profile Statistics

**Endpoint:** `GET /api/profile/stats`

**Response:**
```json
{
  "total_users": 1000,
  "completed_profiles": 750,
  "incomplete_profiles": 250,
  "verified_users": 800,
  "completion_rate": 75.0
}
```

### 7. Validate Profile Data

**Endpoint:** `POST /api/profile/validate`

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "date_of_birth": "1990-01-15T00:00:00Z",
  "gender": "male"
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": []
}
```

## 📊 Profile Completion System

### Completion Levels

1. **Incomplete (0-29%)** - Missing required fields
2. **Basic (30-69%)** - Has basic information
3. **Complete (70-99%)** - Most fields filled
4. **Verified (100%)** - All fields completed

### Field Categories

#### Required Fields (40% of completion)
- `first_name` - User's first name
- `last_name` - User's last name

#### Basic Fields (20% of completion)
- `email` - Email address
- `date_of_birth` - Date of birth
- `gender` - Gender preference

#### Location Fields (10% of completion)
- `country` - Country of residence
- `city` - City of residence

#### Additional Fields (10% of completion)
- `bio` - User biography
- `profile_picture_url` - Profile picture URL

#### Optional Fields (20% of completion)
- `address` - Full address
- `postal_code` - Postal/ZIP code
- `preferences` - User preferences (JSON)

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Profile Configuration
PROFILE_COMPLETION_REQUIRED=true
PROFILE_MIN_COMPLETION_PERCENTAGE=70
PROFILE_AUTO_CREATE_ON_LOGIN=true

# Search Configuration
PROFILE_SEARCH_ENABLED=true
PROFILE_SEARCH_MAX_RESULTS=100

# Validation Configuration
PROFILE_VALIDATION_STRICT=true
PROFILE_AGE_MINIMUM=13
```

## 🛡️ Security & Privacy

### Data Validation
- **Email Validation** - RFC compliant email format
- **Phone Number Validation** - International format required
- **Date Validation** - Age restrictions (minimum 13 years)
- **Name Validation** - Proper formatting and length limits
- **Postal Code Validation** - Format validation

### Privacy Controls
- **Profile Visibility** - Control who can see your profile
- **Search Privacy** - Opt-out of user search
- **Data Retention** - Automatic cleanup of inactive profiles
- **GDPR Compliance** - Data export and deletion support

### Access Control
- **Authentication Required** - All profile endpoints require valid JWT
- **Ownership Validation** - Users can only modify their own profiles
- **Admin Override** - Admin users can manage any profile

## 🧪 Testing

### Manual Testing with cURL

#### 1. Complete Profile
```bash
curl -X POST "http://localhost:8090/api/profile/complete" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_data": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "date_of_birth": "1990-01-15T00:00:00Z",
      "gender": "male",
      "country": "United States",
      "city": "New York",
      "bio": "Software developer"
    }
  }'
```

#### 2. Get Profile
```bash
curl -X GET "http://localhost:8090/api/profile/me" \
  -H "Authorization: Bearer <access_token>"
```

#### 3. Update Profile
```bash
curl -X PUT "http://localhost:8090/api/profile/me" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "bio": "Updated bio"
  }'
```

#### 4. Search Users
```bash
curl -X GET "http://localhost:8090/api/profile/search?query=john&limit=10" \
  -H "Authorization: Bearer <access_token>"
```

### Unit Testing

```python
import pytest
from fastapi.testclient import TestClient
from src.core.application import get_app

client = TestClient(get_app())

def test_complete_profile():
    # First login to get token
    login_response = client.post("/api/auth/login", json={
        "phone_number": "+1234567890",
        "otp_code": "123456"
    })
    token = login_response.json()["access_token"]
    
    # Complete profile
    profile_data = {
        "profile_data": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
    }
    
    response = client.post(
        "/api/profile/complete",
        json=profile_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["profile_completion_percentage"] > 0

def test_get_profile():
    # Get profile
    response = client.get(
        "/api/profile/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"
    assert response.json()["last_name"] == "Doe"
```

## 🚀 Integration Examples

### Frontend Integration

#### React/JavaScript
```javascript
// Complete profile after login
const completeProfile = async (profileData) => {
  const response = await fetch('/api/profile/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ profile_data: profileData })
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log(`Profile ${result.profile_completion_percentage}% complete`);
    // Update UI based on completion status
  }
};

// Check if profile completion is required
const checkProfileStatus = async () => {
  const response = await fetch('/api/profile/completion-status', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  const status = await response.json();
  
  if (status.completion_percentage < 70) {
    // Show profile completion form
    showProfileCompletionForm();
  }
};
```

#### Mobile App (React Native)
```javascript
// Complete profile in mobile app
const completeUserProfile = async (profileData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/complete`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ profile_data: profileData })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Navigate to main app
      navigation.navigate('MainApp');
    } else {
      // Show error message
      Alert.alert('Error', result.message);
    }
  } catch (error) {
    console.error('Profile completion error:', error);
  }
};
```

### Backend Integration

#### Python Client
```python
import requests

class ProfileClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def complete_profile(self, profile_data):
        response = requests.post(
            f'{self.base_url}/api/profile/complete',
            json={'profile_data': profile_data},
            headers=self.headers
        )
        return response.json()
    
    def get_profile(self):
        response = requests.get(
            f'{self.base_url}/api/profile/me',
            headers=self.headers
        )
        return response.json()
    
    def update_profile(self, profile_data):
        response = requests.put(
            f'{self.base_url}/api/profile/me',
            json=profile_data,
            headers=self.headers
        )
        return response.json()

# Usage
client = ProfileClient('http://localhost:8090', access_token)
profile = client.complete_profile({
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john.doe@example.com'
})
```

## 📈 Analytics & Monitoring

### Profile Completion Metrics
- **Completion Rate** - Percentage of users with complete profiles
- **Completion Time** - Average time to complete profile
- **Drop-off Points** - Where users abandon profile completion
- **Field Completion** - Which fields are most/least completed

### User Engagement
- **Profile Views** - How often profiles are viewed
- **Search Usage** - User search patterns
- **Update Frequency** - How often profiles are updated
- **Verification Rate** - Percentage of verified users

### Performance Metrics
- **API Response Times** - Profile endpoint performance
- **Database Query Performance** - Profile query optimization
- **Search Performance** - Full-text search efficiency
- **Cache Hit Rates** - Redis caching effectiveness

## 🔍 Troubleshooting

### Common Issues

#### 1. Profile Not Found
**Error:** `PROFILE_NOT_FOUND`
**Solution:** Complete profile first using `/api/profile/complete`

#### 2. Validation Errors
**Error:** `VALIDATION_ERROR`
**Solution:** Check field formats and requirements

#### 3. Permission Denied
**Error:** `UNAUTHORIZED`
**Solution:** Ensure valid JWT token in Authorization header

#### 4. Search Not Working
**Error:** `USER_SEARCH_FAILED`
**Solution:** Check database indexes and full-text search configuration

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

This will show:
- Profile completion calculations
- Database query details
- Validation results
- Search query performance

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Validation](https://pydantic-docs.helpmanual.io/)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [JWT Token Guide](https://jwt.io/introduction/)
- [Database Migration Best Practices](https://docs.djangoproject.com/en/stable/topics/migrations/)

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs`
- Review the logs for debugging information
- Contact the development team

## 🔄 Version History

- **v1.0.0** - Initial profile system release
  - Basic profile creation and management
  - Completion tracking and validation
  - User search functionality
  - Integration with authentication system
