-- Migration: Create users table for mobile authentication
-- Created: 2024-01-01
-- Description: Creates the users table to store user information for mobile number-based authentication

CREATE TABLE IF NOT EXISTS nal.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON nal.users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON nal.users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON nal.users(last_login);

-- Create a function to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON nal.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON nal.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE nal.users IS 'Stores user information for mobile number-based authentication';
COMMENT ON COLUMN nal.users.user_id IS 'Unique identifier for the user';
COMMENT ON COLUMN nal.users.phone_number IS 'User phone number in international format (e.g., +1234567890)';
COMMENT ON COLUMN nal.users.is_verified IS 'Whether the phone number has been verified via OTP';
COMMENT ON COLUMN nal.users.created_at IS 'Timestamp when the user account was created';
COMMENT ON COLUMN nal.users.last_login IS 'Timestamp of the user last login';
COMMENT ON COLUMN nal.users.updated_at IS 'Timestamp when the record was last updated';
