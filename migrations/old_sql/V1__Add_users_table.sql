-- Ensure the schema exists (CockroachDB supports this syntax)
CREATE SCHEMA IF NOT EXISTS dev_schema;

-- Create the 'users' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email STRING UNIQUE,
    phone_number STRING UNIQUE,
    first_name STRING,
    last_name STRING,
    m_pin STRING CHECK (LENGTH(m_pin) = 4),
    phone_lock BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create an index on the 'email' column if it doesn't exist
CREATE INDEX IF NOT EXISTS users_email_idx ON dev_schema.users (email);
CREATE INDEX IF NOT EXISTS users_phone_number_idx ON dev_schema.users (phone_number);
