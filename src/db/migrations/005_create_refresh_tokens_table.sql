-- Migration: Create refresh tokens table
-- Created: 2024-01-01
-- Description: Creates the refresh_tokens table to store and manage refresh tokens

-- Create refresh tokens table
CREATE TABLE IF NOT EXISTS nal.refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES nal.users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON nal.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON nal.refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON nal.refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_is_revoked ON nal.refresh_tokens(is_revoked);

-- Note: No trigger needed for refresh_tokens table as it doesn't have updated_at column

-- Create function to store refresh token
CREATE OR REPLACE FUNCTION store_refresh_token(
    p_user_id UUID,
    p_token_hash VARCHAR(255),
    p_expires_at TIMESTAMP WITH TIME ZONE
)
RETURNS INTEGER AS $$
DECLARE
    token_id INTEGER;
BEGIN
    -- Revoke any existing active refresh tokens for this user
    UPDATE nal.refresh_tokens 
    SET is_revoked = TRUE, revoked_at = NOW()
    WHERE user_id = p_user_id AND is_revoked = FALSE;
    
    -- Insert new refresh token
    INSERT INTO nal.refresh_tokens (user_id, token_hash, expires_at)
    VALUES (p_user_id, p_token_hash, p_expires_at)
    RETURNING id INTO token_id;
    
    RETURN token_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to verify refresh token
CREATE OR REPLACE FUNCTION verify_refresh_token(
    p_token_hash VARCHAR(255)
)
RETURNS JSONB AS $$
DECLARE
    token_record RECORD;
    result JSONB;
BEGIN
    -- Get the refresh token record
    SELECT rt.*, u.phone_number
    INTO token_record
    FROM nal.refresh_tokens rt
    JOIN nal.users u ON rt.user_id = u.user_id
    WHERE rt.token_hash = p_token_hash
    AND rt.is_revoked = FALSE
    AND rt.expires_at > NOW();
    
    -- If no valid token found
    IF token_record IS NULL THEN
        result := jsonb_build_object(
            'success', false,
            'message', 'Invalid or expired refresh token',
            'error_code', 'INVALID_REFRESH_TOKEN'
        );
        RETURN result;
    END IF;
    
    result := jsonb_build_object(
        'success', true,
        'user_id', token_record.user_id,
        'phone_number', token_record.phone_number,
        'token_id', token_record.id
    );
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to revoke refresh token
CREATE OR REPLACE FUNCTION revoke_refresh_token(
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- Revoke all active refresh tokens for this user
    UPDATE nal.refresh_tokens 
    SET is_revoked = TRUE, revoked_at = NOW()
    WHERE user_id = p_user_id AND is_revoked = FALSE;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    RETURN updated_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Create function to revoke specific refresh token
CREATE OR REPLACE FUNCTION revoke_specific_refresh_token(
    p_token_hash VARCHAR(255)
)
RETURNS BOOLEAN AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- Revoke the specific refresh token
    UPDATE nal.refresh_tokens 
    SET is_revoked = TRUE, revoked_at = NOW()
    WHERE token_hash = p_token_hash AND is_revoked = FALSE;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    RETURN updated_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean up expired refresh tokens
CREATE OR REPLACE FUNCTION cleanup_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired refresh tokens (older than 30 days)
    DELETE FROM nal.refresh_tokens 
    WHERE expires_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE nal.refresh_tokens IS 'Stores refresh tokens for user authentication';
COMMENT ON COLUMN nal.refresh_tokens.user_id IS 'Foreign key reference to users table';
COMMENT ON COLUMN nal.refresh_tokens.token_hash IS 'Hashed refresh token for security';
COMMENT ON COLUMN nal.refresh_tokens.expires_at IS 'When the refresh token expires';
COMMENT ON COLUMN nal.refresh_tokens.is_revoked IS 'Whether the refresh token has been revoked';
COMMENT ON COLUMN nal.refresh_tokens.created_at IS 'When the refresh token was created';
COMMENT ON COLUMN nal.refresh_tokens.revoked_at IS 'When the refresh token was revoked';
