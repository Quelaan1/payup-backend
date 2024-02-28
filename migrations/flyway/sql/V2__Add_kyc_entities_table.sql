-- Ensure the schema exists (CockroachDB supports this syntax)
CREATE SCHEMA IF NOT EXISTS dev_schema;

-- Create the 'kyc_entities' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.kyc_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id STRING UNIQUE,
    entity_name STRING,
    owner_id UUID NOT NULL REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    verified BOOLEAN DEFAULT false,
    entity_type INT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes on 'entity_id' if they don't exist
CREATE INDEX IF NOT EXISTS kyc_entities_entity_type_id_idx ON dev_schema.kyc_entities (entity_type ASC, entity_id);

