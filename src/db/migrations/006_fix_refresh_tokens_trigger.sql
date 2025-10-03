-- Migration: Fix refresh tokens trigger
-- Created: 2024-01-01
-- Description: Removes the incorrect trigger from refresh_tokens table

-- Drop the incorrect trigger
DROP TRIGGER IF EXISTS update_refresh_tokens_updated_at ON nal.refresh_tokens;
