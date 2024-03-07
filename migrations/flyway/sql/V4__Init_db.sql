-- Ensure the schema exists (CockroachDB supports this syntax)
CREATE SCHEMA IF NOT EXISTS dev_schema;

-- drop old tables
DROP TABLE IF EXISTS dev_schema.users;
DROP TABLE IF EXISTS dev_schema.kyc_entities;
DROP TABLE IF EXISTS dev_schema.users;

-- Create the 'users' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type SMALLINT,
    is_active BOOLEAN DEFAULT FALSE,
    phone_lock BOOLEAN DEFAULT FALSE,
    profile_id UUID REFERENCES dev_schema.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email STRING UNIQUE,
    first_name STRING,
    last_name STRING,
    kyc_complete BOOLEAN DEFAULT FALSE,
    onboarded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.kyc_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id STRING UNIQUE,
    entity_name STRING,
    verified BOOLEAN DEFAULT FALSE,
    entity_type SMALLINT,
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    m_otp INT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.phone_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    m_number STRING UNIQUE,
    m_pin STRING,
    verified BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
-- Create an index on the 'email' column if it doesn't exist
CREATE INDEX IF NOT EXISTS profiles_email_idx ON dev_schema.profiles (email);
CREATE INDEX IF NOT EXISTS kyc_entities_entity_idx ON dev_schema.kyc_entities (entity_id);
CREATE INDEX IF NOT EXISTS phone_entities_m_number_idx ON dev_schema.phone_entities (m_number);