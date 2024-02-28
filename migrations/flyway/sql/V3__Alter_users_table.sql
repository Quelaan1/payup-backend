-- Alter the 'users' table ,add columns if it doesn't exist
ALTER TABLE dev_schema.users 
    ADD COLUMN IF NOT EXISTS kyc_complete BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE dev_schema.users 
    ADD COLUMN IF NOT EXISTS onboarded BOOLEAN NOT NULL DEFAULT false;