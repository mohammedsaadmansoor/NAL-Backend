-- Migration: Create OTP table for storing OTP codes
-- Created: 2024-01-01
-- Description: Creates the otp_codes table to store OTP codes and rate limiting data

-- Create OTP codes table
CREATE TABLE IF NOT EXISTS nal.otp_codes (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    is_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE
);

-- Create rate limiting table
CREATE TABLE IF NOT EXISTS nal.rate_limits (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    request_type VARCHAR(50) NOT NULL DEFAULT 'otp',
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    window_duration_minutes INTEGER DEFAULT 15,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone_number, request_type, window_start)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_otp_codes_phone_number ON nal.otp_codes(phone_number);
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires_at ON nal.otp_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_codes_created_at ON nal.otp_codes(created_at);
CREATE INDEX IF NOT EXISTS idx_otp_codes_is_verified ON nal.otp_codes(is_verified);

CREATE INDEX IF NOT EXISTS idx_rate_limits_phone_number ON nal.rate_limits(phone_number);
CREATE INDEX IF NOT EXISTS idx_rate_limits_request_type ON nal.rate_limits(request_type);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON nal.rate_limits(window_start);

-- Create trigger to automatically update the updated_at column for rate_limits
DROP TRIGGER IF EXISTS update_rate_limits_updated_at ON nal.rate_limits;
CREATE TRIGGER update_rate_limits_updated_at
    BEFORE UPDATE ON nal.rate_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired OTP codes
CREATE OR REPLACE FUNCTION cleanup_expired_otp_codes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM nal.otp_codes 
    WHERE expires_at < NOW() 
    AND is_verified = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also clean up old rate limit records (older than 24 hours)
    DELETE FROM nal.rate_limits 
    WHERE window_start < NOW() - INTERVAL '24 hours';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to check rate limit
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_phone_number VARCHAR(20),
    p_request_type VARCHAR(50) DEFAULT 'otp',
    p_window_minutes INTEGER DEFAULT 15,
    p_max_requests INTEGER DEFAULT 1
)
RETURNS BOOLEAN AS $$
DECLARE
    current_count INTEGER;
    window_start_time TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get the current window start time
    window_start_time := NOW() - INTERVAL '1 minute' * p_window_minutes;
    
    -- Get current request count within the window
    SELECT COALESCE(SUM(request_count), 0)
    INTO current_count
    FROM nal.rate_limits
    WHERE phone_number = p_phone_number
    AND request_type = p_request_type
    AND window_start >= window_start_time;
    
    -- If under the limit, allow the request
    IF current_count < p_max_requests THEN
        -- Insert or update rate limit record
        INSERT INTO nal.rate_limits (phone_number, request_type, request_count, window_start, window_duration_minutes)
        VALUES (p_phone_number, p_request_type, 1, NOW(), p_window_minutes)
        ON CONFLICT (phone_number, request_type, window_start) 
        DO UPDATE SET 
            request_count = nal.rate_limits.request_count + 1,
            updated_at = NOW();
        
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create function to store OTP code
CREATE OR REPLACE FUNCTION store_otp_code(
    p_phone_number VARCHAR(20),
    p_otp_code VARCHAR(10),
    p_expiry_minutes INTEGER DEFAULT 5
)
RETURNS INTEGER AS $$
DECLARE
    otp_id INTEGER;
BEGIN
    -- Clean up any existing unverified OTPs for this phone number
    DELETE FROM nal.otp_codes 
    WHERE phone_number = p_phone_number 
    AND is_verified = FALSE;
    
    -- Insert new OTP code
    INSERT INTO nal.otp_codes (phone_number, otp_code, expires_at)
    VALUES (p_phone_number, p_otp_code, NOW() + INTERVAL '1 minute' * p_expiry_minutes)
    RETURNING id INTO otp_id;
    
    RETURN otp_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to verify OTP code
CREATE OR REPLACE FUNCTION verify_otp_code(
    p_phone_number VARCHAR(20),
    p_otp_code VARCHAR(10)
)
RETURNS JSONB AS $$
DECLARE
    otp_record RECORD;
    result JSONB;
BEGIN
    -- Get the most recent unverified OTP for this phone number
    SELECT * INTO otp_record
    FROM nal.otp_codes
    WHERE phone_number = p_phone_number
    AND is_verified = FALSE
    AND expires_at > NOW()
    ORDER BY created_at DESC
    LIMIT 1;
    
    -- If no OTP found
    IF otp_record IS NULL THEN
        result := jsonb_build_object(
            'success', false,
            'message', 'OTP expired or not found',
            'error_code', 'OTP_EXPIRED'
        );
        RETURN result;
    END IF;
    
    -- Check if max attempts exceeded
    IF otp_record.attempts >= otp_record.max_attempts THEN
        -- Mark as expired by setting expires_at to past
        UPDATE nal.otp_codes 
        SET expires_at = NOW() - INTERVAL '1 second'
        WHERE id = otp_record.id;
        
        result := jsonb_build_object(
            'success', false,
            'message', 'Maximum OTP attempts exceeded',
            'error_code', 'MAX_ATTEMPTS_EXCEEDED'
        );
        RETURN result;
    END IF;
    
    -- Check if OTP code matches
    IF otp_record.otp_code = p_otp_code THEN
        -- Mark as verified
        UPDATE nal.otp_codes 
        SET is_verified = TRUE, verified_at = NOW()
        WHERE id = otp_record.id;
        
        result := jsonb_build_object(
            'success', true,
            'message', 'OTP verified successfully',
            'otp_id', otp_record.id
        );
        RETURN result;
    ELSE
        -- Increment attempts
        UPDATE nal.otp_codes 
        SET attempts = attempts + 1
        WHERE id = otp_record.id;
        
        result := jsonb_build_object(
            'success', false,
            'message', 'Invalid OTP code',
            'error_code', 'INVALID_OTP',
            'attempts_remaining', otp_record.max_attempts - otp_record.attempts - 1
        );
        RETURN result;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE nal.otp_codes IS 'Stores OTP codes for phone number verification';
COMMENT ON COLUMN nal.otp_codes.phone_number IS 'Phone number in international format';
COMMENT ON COLUMN nal.otp_codes.otp_code IS 'The OTP code sent to the user';
COMMENT ON COLUMN nal.otp_codes.attempts IS 'Number of verification attempts made';
COMMENT ON COLUMN nal.otp_codes.max_attempts IS 'Maximum allowed verification attempts';
COMMENT ON COLUMN nal.otp_codes.is_verified IS 'Whether the OTP has been successfully verified';
COMMENT ON COLUMN nal.otp_codes.expires_at IS 'When the OTP expires';
COMMENT ON COLUMN nal.otp_codes.created_at IS 'When the OTP was created';
COMMENT ON COLUMN nal.otp_codes.verified_at IS 'When the OTP was verified';

COMMENT ON TABLE nal.rate_limits IS 'Stores rate limiting information for API requests';
COMMENT ON COLUMN nal.rate_limits.phone_number IS 'Phone number for rate limiting';
COMMENT ON COLUMN nal.rate_limits.request_type IS 'Type of request (e.g., otp, login)';
COMMENT ON COLUMN nal.rate_limits.request_count IS 'Number of requests in the current window';
COMMENT ON COLUMN nal.rate_limits.window_start IS 'Start of the rate limiting window';
COMMENT ON COLUMN nal.rate_limits.window_duration_minutes IS 'Duration of the rate limiting window in minutes';
