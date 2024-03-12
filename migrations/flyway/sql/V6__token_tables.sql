-- Create the 'refresh_token_entities' table  with ttl

CREATE TABLE IF NOT EXISTS dev_schema.refresh_token_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti UUID,
    expires_on TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(), 
    user_id UUID REFERENCES REFERENCES dev_schema.users(id) ON DELETE CASCADE
) WITH (ttl_expiration_expression = 'expires_on');

-- Create the 'access_token_blacklists' table  with ttl

CREATE TABLE IF NOT EXISTS dev_schema.access_token_blacklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expires_on TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
) WITH (ttl_expiration_expression = 'expires_on');