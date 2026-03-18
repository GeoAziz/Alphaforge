-- Firebase UID Migration for Users Table
-- Adds firebase_uid column to support Firebase authentication integration
-- Safe to run multiple times (uses IF NOT EXISTS pattern)

BEGIN;

-- Add firebase_uid column to users table if it doesn't exist
ALTER TABLE IF EXISTS users
ADD COLUMN IF NOT EXISTS firebase_uid TEXT UNIQUE;

-- Create index on firebase_uid for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);

-- Create index on firebase_uid and email together (useful for authentication flows)
CREATE INDEX IF NOT EXISTS idx_users_firebase_uid_email ON users(firebase_uid, email);

-- Comment explaining the column
COMMENT ON COLUMN users.firebase_uid IS 'Firebase UID linked to this user account. Used for Firebase Authentication integration.';

COMMIT;
