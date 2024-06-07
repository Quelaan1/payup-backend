-- Alter the 'otps' table ,add columns if it doesn't exist
ALTER TABLE dev_schema.otps
ADD COLUMN IF NOT EXISTS attempt_remains SMALLINT NOT NULL DEFAULT 3;