ALTER TABLE dev_schema.kyc_entities 
    DROP COLUMN IF EXISTS user_id,
    DROP CONSTRAINT IF EXISTS kyc_entities_user_id_fkey;
