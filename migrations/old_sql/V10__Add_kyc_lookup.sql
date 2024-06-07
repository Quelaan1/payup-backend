
-- Create the 'kyc_lookups' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.kyc_lookups (
    kyc_entity_id UUID PRIMARY KEY REFERENCES dev_schema.kyc_entities(id) ON DELETE CASCADE,
    entity_id STRING UNIQUE,
    entity_type INT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create an index on the 'entity_id' column if it doesn't exist
CREATE INDEX IF NOT EXISTS kyc_lookups_entity_idx ON dev_schema.kyc_lookups (entity_id);