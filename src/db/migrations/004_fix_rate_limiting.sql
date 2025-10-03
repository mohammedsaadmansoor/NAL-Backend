-- Migration: Fix rate limiting functions
-- Created: 2024-01-01
-- Description: Fixes the rate limiting functions to work properly

-- Drop existing functions
DROP FUNCTION IF EXISTS check_rate_limit(VARCHAR(20), VARCHAR(50), INTEGER, INTEGER);

-- Create a simpler rate limiting function
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
        -- Insert new rate limit record
        INSERT INTO nal.rate_limits (phone_number, request_type, request_count, window_start, window_duration_minutes)
        VALUES (p_phone_number, p_request_type, 1, NOW(), p_window_minutes);
        
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
