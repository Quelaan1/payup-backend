-- Ensure the schema exists (CockroachDB supports this syntax)
CREATE SCHEMA IF NOT EXISTS dev_schema;

-- Create the 'profiles' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email STRING UNIQUE,
    name STRING,
    phone_number STRING UNIQUE,  -- Phone number is now stored here
    kyc_complete BOOLEAN DEFAULT FALSE,
    onboarded BOOLEAN DEFAULT FALSE,
    kyc_pan BOOLEAN NOT NULL DEFAULT false,
    kyc_uidai BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create an index on the 'profiles' table
CREATE INDEX IF NOT EXISTS profiles_email_idx ON dev_schema.profiles (email);

-- Create the 'users' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type SMALLINT,
    is_active BOOLEAN DEFAULT FALSE,
    phone_lock BOOLEAN DEFAULT FALSE,
    profile_id UUID REFERENCES dev_schema.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    kyc_complete BOOLEAN NOT NULL DEFAULT false,
    onboarded BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS dev_schema.devices (
    device_id STRING PRIMARY KEY,
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    device_type STRING,  -- e.g., 'iOS', 'Android', 'Web'
    last_used TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.device_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id STRING REFERENCES dev_schema.devices(device_id) ON DELETE CASCADE,
    token STRING UNIQUE,
    token_purpose STRING,  -- e.g., 'notification', 'mfa', 'analytics'
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create the 'kyc_entities' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.kyc_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id_encrypted STRING UNIQUE,
    entity_name STRING,
    verified BOOLEAN DEFAULT FALSE,
    entity_type SMALLINT,
    email STRING,
    gender STRING,
    zip STRING,
    category STRING,
    birthOrIncorporatedDate STRING,
    status STRING,
    address JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes on 'kyc_entities' table
CREATE INDEX IF NOT EXISTS kyc_entities_entity_type_id_idx ON dev_schema.kyc_entities (entity_type ASC, entity_id_encrypted);

-- Create the 'user_kyc_relations' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.user_kyc_relations (
    kyc_id UUID REFERENCES dev_schema.kyc_entities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (kyc_id, user_id)
);

-- Create the 'kyc_lookups' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.kyc_lookups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id STRING UNIQUE,
    entity_type INT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create an index on the 'kyc_lookups' table
CREATE INDEX IF NOT EXISTS kyc_lookups_entity_idx ON dev_schema.kyc_lookups (entity_id);

-- Create the 'otps' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.otps (
    id UUID PRIMARY KEY REFERENCES dev_schema.profiles(id) ON DELETE CASCADE,  -- Reference to profiles
    m_otp INT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    attempt_remains SMALLINT NOT NULL DEFAULT 3
) WITH (ttl_expiration_expression = 'expires_at');

-- Create the 'refresh_token_entities' table with ttl and device context
CREATE TABLE IF NOT EXISTS dev_schema.refresh_token_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti UUID,
    expires_on TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    device_id STRING REFERENCES dev_schema.devices(device_id) ON DELETE CASCADE  -- Adding device context
) WITH (ttl_expiration_expression = 'expires_on');

-- Create the 'access_token_blacklists' table with ttl and device context
CREATE TABLE IF NOT EXISTS dev_schema.access_token_blacklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expires_on TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,  -- Adding user context
    device_id STRING REFERENCES dev_schema.devices(device_id) ON DELETE CASCADE  -- Adding device context
) WITH (ttl_expiration_expression = 'expires_on');

-- Create the 'promotions' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.promotions (
    id SERIAL PRIMARY KEY,
    discount VARCHAR(50),
    title VARCHAR(100),
    description TEXT,
    image_url VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.notification_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    title TEXT,
    message TEXT,
    type STRING,  -- e.g., 'promotion', 'reminder'
    status STRING,  -- e.g., 'sent', 'failed'
    method STRING,  -- e.g., 'push', 'sms', 'email'
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.payees (
    payee_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES dev_schema.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    upi_id TEXT,
    bank_name TEXT,
    ifsc TEXT,
    account_number TEXT,
    last_paid TIMESTAMPTZ,
    phone_number TEXT NOT NULL,  -- Phone number can be stored here if needed
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dev_schema.profile_payee_relations (
    payee_id UUID NOT NULL,
    profile_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payee_id, profile_id),
    CONSTRAINT fk_payee
        FOREIGN KEY (payee_id)
        REFERENCES dev_schema.payees(payee_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_profile
        FOREIGN KEY (profile_id)
        REFERENCES dev_schema.profiles(id)
        ON DELETE CASCADE
);