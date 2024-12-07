-- Alter the 'profiles' table ,add columns if it doesn't exist
ALTER TABLE dev_schema.profiles 
    ADD COLUMN IF NOT EXISTS kyc_pan BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE dev_schema.profiles 
    ADD COLUMN IF NOT EXISTS kyc_uidai BOOLEAN NOT NULL DEFAULT false;