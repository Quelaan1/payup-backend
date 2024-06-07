
-- drop old tables
DROP TABLE IF EXISTS dev_schema.otps;
-- Re-create the 'otp' table  with ttl

CREATE TABLE IF NOT EXISTS dev_schema.otps (
    id UUID PRIMARY KEY REFERENCES dev_schema.phone_entities(id) ON DELETE CASCADE,
    m_otp INT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
) WITH (ttl_expiration_expression = 'expires_at');

-- ALTER TABLE dev_schema.otps CONFIGURE ZONE USING gc.ttlseconds = 300;
