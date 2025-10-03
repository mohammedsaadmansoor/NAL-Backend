from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from src.db.connection import aget_connection, release_connection
from src.services.utils.exceptions import APIException
from src.utils.logging import get_logger
from src.app.models.user_profile import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    ProfileCompletionStatus, UserStatus, Gender
)

logger = get_logger(__name__)


class UserProfileService:
    """Service for managing user profiles."""
    
    def __init__(self):
        self.required_fields = ['first_name', 'last_name']
        self.basic_fields = ['email', 'date_of_birth', 'gender']
        self.location_fields = ['country', 'city']
        self.additional_fields = ['bio', 'profile_picture_url']
    
    async def create_user_profile(self, user_id: str, profile_data: UserProfileCreate) -> UserProfileResponse:
        """
        Create a new user profile.
        
        Args:
            user_id: User ID
            profile_data: Profile data to create
            
        Returns:
            Created user profile
        """
        try:
            conn = await aget_connection()
            try:
                # Check if profile already exists in user_profiles table
                profile_check_query = "SELECT user_id FROM nal.user_profiles WHERE user_id = $1"
                existing_profile = await conn.fetchrow(profile_check_query, user_id)
                if existing_profile:
                    raise APIException(
                        message="User profile already exists. Use update instead.",
                        error_code="PROFILE_ALREADY_EXISTS",
                        status_code=400
                    )
                
                # Insert new profile
                insert_query = """
                    INSERT INTO nal.user_profiles (
                        user_id, first_name, last_name, email, date_of_birth,
                        gender, country, city, address, postal_code,
                        profile_picture_url, bio, preferences
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                    )
                    RETURNING user_id, first_name, last_name, email, date_of_birth,
                        gender, country, city, address, postal_code,
                        profile_picture_url, bio, preferences, profile_completion_status,
                        profile_completion_percentage, status, created_at, updated_at
                """
                
                # Convert preferences to JSON string
                preferences_json = "{}"
                if profile_data.preferences:
                    import json
                    preferences_json = json.dumps(profile_data.preferences)
                
                profile_row = await conn.fetchrow(
                    insert_query,
                    user_id,
                    profile_data.first_name,
                    profile_data.last_name,
                    profile_data.email,
                    profile_data.date_of_birth,
                    profile_data.gender.value if profile_data.gender else None,
                    profile_data.country,
                    profile_data.city,
                    profile_data.address,
                    profile_data.postal_code,
                    profile_data.profile_picture_url,
                    profile_data.bio,
                    preferences_json
                )
                
                logger.info(f"User profile created for user {user_id}")
                return await self._profile_row_to_response(profile_row, user_id)
                
            finally:
                await release_connection(conn)
                
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            raise APIException(
                message="Failed to create user profile.",
                error_code="PROFILE_CREATION_FAILED",
                status_code=500
            )
    
    async def get_user_profile_by_id(self, user_id: str) -> Optional[UserProfileResponse]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None if not found
        """
        try:
            logger.info(f"Getting user profile for ID: {user_id}")
            conn = await aget_connection()
            logger.info("Database connection acquired")
            try:
                query = """
                    SELECT 
                        u.user_id, u.phone_number, u.is_verified, u.created_at, u.last_login,
                        up.first_name, up.last_name, up.email, up.date_of_birth, up.gender,
                        up.country, up.city, up.address, up.postal_code, up.profile_picture_url,
                        up.bio, up.preferences, up.profile_completion_status,
                        up.profile_completion_percentage, up.status, up.created_at as profile_created_at,
                        up.updated_at
                    FROM nal.users u
                    LEFT JOIN nal.user_profiles up ON u.user_id = up.user_id
                    WHERE u.user_id = $1
                """
                
                row = await conn.fetchrow(query, user_id)
                if not row:
                    logger.info(f"No user found with ID: {user_id}")
                    return None
                
                logger.info(f"Found user row: {dict(row)}")
                return await self._row_to_profile_response(row)
                
            finally:
                await release_connection(conn)
                
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise APIException(
                message="Failed to get user profile.",
                error_code="PROFILE_FETCH_FAILED",
                status_code=500
            )
    
    async def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate) -> UserProfileResponse:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            profile_data: Profile data to update
            
        Returns:
            Updated user profile
        """
        try:
            conn = await aget_connection()
            try:
                # Check if profile exists
                existing_profile = await self.get_user_profile_by_id(user_id)
                if not existing_profile:
                    raise APIException(
                        message="User profile not found. Create profile first.",
                        error_code="PROFILE_NOT_FOUND",
                        status_code=404
                    )
                
                # Build dynamic update query
                update_fields = []
                update_values = []
                param_count = 1
                
                for field, value in profile_data.dict(exclude_unset=True).items():
                    if value is not None:
                        if field == 'gender' and isinstance(value, Gender):
                            value = value.value
                        elif field == 'preferences' and isinstance(value, dict):
                            import json
                            value = json.dumps(value)
                        update_fields.append(f"{field} = ${param_count}")
                        update_values.append(value)
                        param_count += 1
                
                if not update_fields:
                    return existing_profile
                
                # Add updated_at
                update_fields.append(f"updated_at = ${param_count}")
                update_values.append(datetime.now())
                param_count += 1
                
                # Add user_id for WHERE clause
                update_values.append(user_id)
                
                update_query = f"""
                    UPDATE nal.user_profiles 
                    SET {', '.join(update_fields)}
                    WHERE user_id = ${param_count}
                    RETURNING *
                """
                
                profile_row = await conn.fetchrow(update_query, *update_values)
                
                logger.info(f"User profile updated for user {user_id}")
                logger.info(f"Updated profile row: {dict(profile_row) if profile_row else 'None'}")
                return await self._profile_row_to_response(profile_row, user_id)
                
            finally:
                await release_connection(conn)
                
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise APIException(
                message="Failed to update user profile.",
                error_code="PROFILE_UPDATE_FAILED",
                status_code=500
            )
    
    async def complete_user_profile(self, user_id: str, profile_data: UserProfileCreate) -> UserProfileResponse:
        """
        Complete user profile (create or update with complete data).
        
        Args:
            user_id: User ID
            profile_data: Complete profile data
            
        Returns:
            Completed user profile
        """
        try:
            # Check if profile actually exists in user_profiles table
            conn = await aget_connection()
            try:
                profile_check_query = "SELECT user_id FROM nal.user_profiles WHERE user_id = $1"
                profile_exists = await conn.fetchrow(profile_check_query, user_id)
                
                if profile_exists:
                    # Update existing profile
                    update_data = UserProfileUpdate(**profile_data.dict())
                    return await self.update_user_profile(user_id, update_data)
                else:
                    # Create new profile
                    return await self.create_user_profile(user_id, profile_data)
            finally:
                await release_connection(conn)
                
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error completing user profile: {str(e)}")
            raise APIException(
                message="Failed to complete user profile.",
                error_code="PROFILE_COMPLETION_FAILED",
                status_code=500
            )
    
    async def get_profile_completion_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get profile completion status and missing fields.
        
        Args:
            user_id: User ID
            
        Returns:
            Profile completion information
        """
        try:
            profile = await self.get_user_profile_by_id(user_id)
            if not profile:
                return {
                    "completion_status": ProfileCompletionStatus.INCOMPLETE,
                    "completion_percentage": 0,
                    "missing_required_fields": self.required_fields,
                    "missing_basic_fields": self.basic_fields,
                    "missing_location_fields": self.location_fields,
                    "missing_additional_fields": self.additional_fields
                }
            
            missing_fields = []
            profile_dict = profile.dict()
            
            # Check required fields
            for field in self.required_fields:
                if not profile_dict.get(field):
                    missing_fields.append(field)
            
            # Check basic fields
            basic_missing = []
            for field in self.basic_fields:
                if not profile_dict.get(field):
                    basic_missing.append(field)
            
            # Check location fields
            location_missing = []
            for field in self.location_fields:
                if not profile_dict.get(field):
                    location_missing.append(field)
            
            # Check additional fields
            additional_missing = []
            for field in self.additional_fields:
                if not profile_dict.get(field):
                    additional_missing.append(field)
            
            return {
                "completion_status": profile.profile_completion_status,
                "completion_percentage": profile.profile_completion_percentage,
                "missing_required_fields": missing_fields,
                "missing_basic_fields": basic_missing,
                "missing_location_fields": location_missing,
                "missing_additional_fields": additional_missing
            }
            
        except Exception as e:
            logger.error(f"Error getting profile completion status: {str(e)}")
            raise APIException(
                message="Failed to get profile completion status.",
                error_code="COMPLETION_STATUS_FAILED",
                status_code=500
            )
    
    async def search_users(self, query: str, limit: int = 10, offset: int = 0) -> Tuple[List[UserProfileResponse], int]:
        """
        Search users by name or bio.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (users, total_count)
        """
        try:
            conn = await aget_connection()
            try:
                # Full-text search query
                search_query = """
                    SELECT 
                        u.user_id, u.phone_number, u.is_verified, u.created_at, u.last_login,
                        up.first_name, up.last_name, up.email, up.date_of_birth, up.gender,
                        up.country, up.city, up.address, up.postal_code, up.profile_picture_url,
                        up.bio, up.preferences, up.profile_completion_status,
                        up.profile_completion_percentage, up.status, up.created_at as profile_created_at,
                        up.updated_at,
                        ts_rank(to_tsvector('english', 
                            COALESCE(up.first_name, '') || ' ' || 
                            COALESCE(up.last_name, '') || ' ' || 
                            COALESCE(up.bio, '')
                        ), plainto_tsquery('english', $1)) as rank
                    FROM nal.users u
                    LEFT JOIN nal.user_profiles up ON u.user_id = up.user_id
                    WHERE to_tsvector('english', 
                        COALESCE(up.first_name, '') || ' ' || 
                        COALESCE(up.last_name, '') || ' ' || 
                        COALESCE(up.bio, '')
                    ) @@ plainto_tsquery('english', $1)
                    ORDER BY rank DESC, up.updated_at DESC
                    LIMIT $2 OFFSET $3
                """
                
                # Count query
                count_query = """
                    SELECT COUNT(*)
                    FROM nal.users u
                    LEFT JOIN nal.user_profiles up ON u.user_id = up.user_id
                    WHERE to_tsvector('english', 
                        COALESCE(up.first_name, '') || ' ' || 
                        COALESCE(up.last_name, '') || ' ' || 
                        COALESCE(up.bio, '')
                    ) @@ plainto_tsquery('english', $1)
                """
                
                # Execute queries
                rows = await conn.fetch(search_query, query, limit, offset)
                total_count = await conn.fetchval(count_query, query)
                
                users = []
                for row in rows:
                    users.append(await self._row_to_profile_response(row))
                
                return users, total_count
                
            finally:
                await release_connection(conn)
                
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise APIException(
                message="Failed to search users.",
                error_code="USER_SEARCH_FAILED",
                status_code=500
            )
    
    async def get_profile_statistics(self) -> Dict[str, Any]:
        """
        Get profile completion statistics.
        
        Returns:
            Profile statistics
        """
        try:
            conn = await aget_connection()
            try:
                stats_query = """
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN up.profile_completion_status = 'complete' OR up.profile_completion_status = 'verified' THEN 1 END) as completed_profiles,
                        COUNT(CASE WHEN up.profile_completion_status = 'incomplete' OR up.profile_completion_status = 'basic' THEN 1 END) as incomplete_profiles,
                        COUNT(CASE WHEN u.is_verified = true THEN 1 END) as verified_users,
                        AVG(up.profile_completion_percentage) as avg_completion_percentage
                    FROM nal.users u
                    LEFT JOIN nal.user_profiles up ON u.user_id = up.user_id
                """
                
                stats = await conn.fetchrow(stats_query)
                
                completion_rate = 0
                if stats['total_users'] > 0:
                    completion_rate = (stats['completed_profiles'] / stats['total_users']) * 100
                
                return {
                    "total_users": stats['total_users'],
                    "completed_profiles": stats['completed_profiles'],
                    "incomplete_profiles": stats['incomplete_profiles'],
                    "verified_users": stats['verified_users'],
                    "completion_rate": round(completion_rate, 2),
                    "average_completion_percentage": round(float(stats['avg_completion_percentage'] or 0), 2)
                }
                
            finally:
                await release_connection(conn)
                
        except Exception as e:
            logger.error(f"Error getting profile statistics: {str(e)}")
            raise APIException(
                message="Failed to get profile statistics.",
                error_code="STATS_FETCH_FAILED",
                status_code=500
            )
    
    async def _row_to_profile_response(self, row) -> UserProfileResponse:
        """Convert database row to UserProfileResponse."""
        try:
            # Handle gender enum
            gender = None
            if row.get('gender'):
                try:
                    gender = Gender(row['gender'])
                except ValueError:
                    gender = None
            
            # Handle completion status enum
            completion_status = ProfileCompletionStatus.INCOMPLETE
            if row.get('profile_completion_status'):
                try:
                    completion_status = ProfileCompletionStatus(row['profile_completion_status'])
                except ValueError:
                    completion_status = ProfileCompletionStatus.INCOMPLETE
            
            # Handle user status enum
            status = UserStatus.ACTIVE
            if row.get('status'):
                try:
                    status = UserStatus(row['status'])
                except ValueError:
                    status = UserStatus.ACTIVE
            
            # Handle preferences - ensure it's a dict
            preferences = row.get('preferences')
            if preferences is None:
                preferences = {}
            elif isinstance(preferences, str):
                try:
                    import json
                    preferences = json.loads(preferences)
                except (json.JSONDecodeError, TypeError):
                    preferences = {}
            elif not isinstance(preferences, dict):
                preferences = {}
            
            return UserProfileResponse(
                user_id=str(row['user_id']),
                phone_number=row['phone_number'],
                first_name=row.get('first_name'),
                last_name=row.get('last_name'),
                email=row.get('email'),
                date_of_birth=row.get('date_of_birth'),
                gender=gender,
                country=row.get('country'),
                city=row.get('city'),
                address=row.get('address'),
                postal_code=row.get('postal_code'),
                profile_picture_url=row.get('profile_picture_url'),
                bio=row.get('bio'),
                preferences=preferences,
                profile_completion_status=completion_status,
                profile_completion_percentage=row.get('profile_completion_percentage') or 0,
                is_verified=row.get('is_verified', False),
                status=status,
                created_at=row.get('profile_created_at') or row['created_at'],
                updated_at=row.get('updated_at') or row['created_at'],
                last_login=row.get('last_login')
            )
            
        except Exception as e:
            logger.error(f"Error converting row to profile response: {str(e)}")
            logger.error(f"Row data: {dict(row) if row else 'None'}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise APIException(
                message="Failed to process profile data.",
                error_code="PROFILE_PROCESSING_FAILED",
                status_code=500
            )
    
    async def _profile_row_to_response(self, profile_row, user_id: str) -> UserProfileResponse:
        """Convert user_profiles table row to UserProfileResponse."""
        try:
            # Get user info from users table
            conn = await aget_connection()
            try:
                user_query = """
                    SELECT user_id, phone_number, is_verified, created_at, last_login
                    FROM nal.users 
                    WHERE user_id = $1
                """
                user_row = await conn.fetchrow(user_query, user_id)
                
                if not user_row:
                    raise APIException(
                        message="User not found.",
                        error_code="USER_NOT_FOUND",
                        status_code=404
                    )
                
                # Handle gender enum
                gender = None
                if profile_row.get('gender'):
                    try:
                        gender = Gender(profile_row['gender'])
                    except ValueError:
                        gender = None
                
                # Handle completion status enum
                completion_status = ProfileCompletionStatus.INCOMPLETE
                if profile_row.get('profile_completion_status'):
                    try:
                        completion_status = ProfileCompletionStatus(profile_row['profile_completion_status'])
                    except ValueError:
                        completion_status = ProfileCompletionStatus.INCOMPLETE
                
                # Handle user status enum
                status = UserStatus.ACTIVE
                if profile_row.get('status'):
                    try:
                        status = UserStatus(profile_row['status'])
                    except ValueError:
                        status = UserStatus.ACTIVE
                
                # Handle preferences - ensure it's a dict
                preferences = profile_row.get('preferences')
                if preferences is None:
                    preferences = {}
                elif isinstance(preferences, str):
                    try:
                        import json
                        preferences = json.loads(preferences)
                    except (json.JSONDecodeError, TypeError):
                        preferences = {}
                elif not isinstance(preferences, dict):
                    preferences = {}
                
                return UserProfileResponse(
                    user_id=str(user_row['user_id']),
                    phone_number=user_row['phone_number'],
                    first_name=profile_row.get('first_name'),
                    last_name=profile_row.get('last_name'),
                    email=profile_row.get('email'),
                    date_of_birth=profile_row.get('date_of_birth'),
                    gender=gender,
                    country=profile_row.get('country'),
                    city=profile_row.get('city'),
                    address=profile_row.get('address'),
                    postal_code=profile_row.get('postal_code'),
                    profile_picture_url=profile_row.get('profile_picture_url'),
                    bio=profile_row.get('bio'),
                    preferences=preferences,
                    profile_completion_status=completion_status,
                    profile_completion_percentage=profile_row.get('profile_completion_percentage') or 0,
                    is_verified=user_row.get('is_verified', False),
                    status=status,
                    created_at=profile_row.get('created_at') or user_row['created_at'],
                    updated_at=profile_row.get('updated_at') or user_row['created_at'],
                    last_login=user_row.get('last_login')
                )
                
            finally:
                await release_connection(conn)
            
        except Exception as e:
            logger.error(f"Error converting profile row to response: {str(e)}")
            logger.error(f"Profile row data: {dict(profile_row) if profile_row else 'None'}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise APIException(
                message="Failed to process profile data.",
                error_code="PROFILE_PROCESSING_FAILED",
                status_code=500
            )


# Global user profile service instance
user_profile_service = UserProfileService()
