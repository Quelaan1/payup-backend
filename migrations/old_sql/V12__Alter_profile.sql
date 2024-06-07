-- Alter the 'profiles' table ,add columns if it doesn't exist
ALTER TABLE dev_schema.profiles 
    RENAME COLUMN first_name TO name;

ALTER TABLE dev_schema.profiles 
    DROP COLUMN IF EXISTS last_name;

ALTER TABLE dev_schema.kyc_entities
    ADD COLUMN IF NOT EXISTS address JSONB;



