-- Alter the 'kyc_entities' table ,add columns if it doesn't exist
ALTER TABLE dev_schema.kyc_entities 
    ADD COLUMN IF NOT EXISTS entity_id_encrypted BYTES UNIQUE,
    ADD COLUMN IF NOT EXISTS email STRING,
    ADD COLUMN IF NOT EXISTS gender STRING,
    ADD COLUMN IF NOT EXISTS pincode STRING,
    ADD COLUMN IF NOT EXISTS category STRING,
    ADD COLUMN IF NOT EXISTS status STRING,

ALTER TABLE dev_schema.kyc_entities 
    DROP COLUMN IF EXISTS entity_id;