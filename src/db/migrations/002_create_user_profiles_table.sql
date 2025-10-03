-- Migration: Create user profiles table
-- Created: 2024-01-01
-- Description: Creates the user_profiles table to store detailed user profile information

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS nal.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES nal.users(user_id) ON DELETE CASCADE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(255) UNIQUE,
    date_of_birth DATE,
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    country VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    postal_code VARCHAR(20),
    profile_picture_url TEXT,
    bio TEXT,
    preferences JSONB DEFAULT '{}',
    profile_completion_status VARCHAR(20) DEFAULT 'incomplete' CHECK (profile_completion_status IN ('incomplete', 'basic', 'complete', 'verified')),
    profile_completion_percentage INTEGER DEFAULT 0 CHECK (profile_completion_percentage >= 0 AND profile_completion_percentage <= 100),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending_verification')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON nal.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON nal.user_profiles(country);
CREATE INDEX IF NOT EXISTS idx_user_profiles_city ON nal.user_profiles(city);
CREATE INDEX IF NOT EXISTS idx_user_profiles_status ON nal.user_profiles(status);
CREATE INDEX IF NOT EXISTS idx_user_profiles_completion_status ON nal.user_profiles(profile_completion_status);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON nal.user_profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at ON nal.user_profiles(updated_at);

-- Create full-text search index for user names and bio
CREATE INDEX IF NOT EXISTS idx_user_profiles_search ON nal.user_profiles USING gin(
    to_tsvector('english', 
        COALESCE(first_name, '') || ' ' || 
        COALESCE(last_name, '') || ' ' || 
        COALESCE(bio, '')
    )
);

-- Create trigger to automatically update the updated_at column
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON nal.user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON nal.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to calculate profile completion percentage
CREATE OR REPLACE FUNCTION calculate_profile_completion_percentage(profile_row nal.user_profiles)
RETURNS INTEGER AS $$
DECLARE
    completion_score INTEGER := 0;
    total_fields INTEGER := 10; -- Total number of profile fields
BEGIN
    -- Basic required fields (40% of completion)
    IF profile_row.first_name IS NOT NULL AND profile_row.first_name != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    IF profile_row.last_name IS NOT NULL AND profile_row.last_name != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    -- Contact information (20% of completion)
    IF profile_row.email IS NOT NULL AND profile_row.email != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    -- Personal information (20% of completion)
    IF profile_row.date_of_birth IS NOT NULL THEN
        completion_score := completion_score + 1;
    END IF;
    
    IF profile_row.gender IS NOT NULL THEN
        completion_score := completion_score + 1;
    END IF;
    
    -- Location information (10% of completion)
    IF profile_row.country IS NOT NULL AND profile_row.country != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    IF profile_row.city IS NOT NULL AND profile_row.city != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    -- Additional information (10% of completion)
    IF profile_row.bio IS NOT NULL AND profile_row.bio != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    IF profile_row.profile_picture_url IS NOT NULL AND profile_row.profile_picture_url != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    -- Address is optional but adds to completion
    IF profile_row.address IS NOT NULL AND profile_row.address != '' THEN
        completion_score := completion_score + 1;
    END IF;
    
    -- Calculate percentage
    RETURN (completion_score * 100) / total_fields;
END;
$$ LANGUAGE plpgsql;

-- Create function to determine profile completion status
CREATE OR REPLACE FUNCTION determine_profile_completion_status(completion_percentage INTEGER)
RETURNS VARCHAR(20) AS $$
BEGIN
    IF completion_percentage = 0 THEN
        RETURN 'incomplete';
    ELSIF completion_percentage < 30 THEN
        RETURN 'incomplete';
    ELSIF completion_percentage < 70 THEN
        RETURN 'basic';
    ELSIF completion_percentage < 100 THEN
        RETURN 'complete';
    ELSE
        RETURN 'verified';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update completion percentage and status
CREATE OR REPLACE FUNCTION update_profile_completion()
RETURNS TRIGGER AS $$
DECLARE
    new_percentage INTEGER;
    new_status VARCHAR(20);
BEGIN
    -- Calculate new completion percentage
    new_percentage := calculate_profile_completion_percentage(NEW);
    
    -- Determine new status
    new_status := determine_profile_completion_status(new_percentage);
    
    -- Update the fields
    NEW.profile_completion_percentage := new_percentage;
    NEW.profile_completion_status := new_status;
    NEW.updated_at := NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for profile completion updates
DROP TRIGGER IF EXISTS trigger_update_profile_completion ON nal.user_profiles;
CREATE TRIGGER trigger_update_profile_completion
    BEFORE INSERT OR UPDATE ON nal.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_profile_completion();

-- Add comments for documentation
COMMENT ON TABLE nal.user_profiles IS 'Stores detailed user profile information';
COMMENT ON COLUMN nal.user_profiles.user_id IS 'Foreign key reference to users table';
COMMENT ON COLUMN nal.user_profiles.first_name IS 'User first name';
COMMENT ON COLUMN nal.user_profiles.last_name IS 'User last name';
COMMENT ON COLUMN nal.user_profiles.email IS 'User email address (unique)';
COMMENT ON COLUMN nal.user_profiles.date_of_birth IS 'User date of birth';
COMMENT ON COLUMN nal.user_profiles.gender IS 'User gender preference';
COMMENT ON COLUMN nal.user_profiles.country IS 'User country';
COMMENT ON COLUMN nal.user_profiles.city IS 'User city';
COMMENT ON COLUMN nal.user_profiles.address IS 'User address';
COMMENT ON COLUMN nal.user_profiles.postal_code IS 'User postal code';
COMMENT ON COLUMN nal.user_profiles.profile_picture_url IS 'URL to user profile picture';
COMMENT ON COLUMN nal.user_profiles.bio IS 'User biography/description';
COMMENT ON COLUMN nal.user_profiles.preferences IS 'User preferences stored as JSON';
COMMENT ON COLUMN nal.user_profiles.profile_completion_status IS 'Profile completion status';
COMMENT ON COLUMN nal.user_profiles.profile_completion_percentage IS 'Profile completion percentage (0-100)';
COMMENT ON COLUMN nal.user_profiles.status IS 'User account status';
COMMENT ON COLUMN nal.user_profiles.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN nal.user_profiles.updated_at IS 'Profile last update timestamp';
