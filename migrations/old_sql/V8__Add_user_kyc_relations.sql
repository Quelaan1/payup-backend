
-- Create the 'user_kyc_relations' table if it doesn't exist

CREATE TABLE IF NOT EXISTS dev_schema.user_kyc_relations (
    kyc_id UUID REFERENCES dev_schema.kyc_entities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (kyc_id, user_id)
);