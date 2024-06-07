-- Ensure the schema exists (CockroachDB supports this syntax)
CREATE SCHEMA IF NOT EXISTS dev_schema;

-- Create the 'dev_schema.promotions' table if it doesn't exist
CREATE TABLE IF NOT EXISTS dev_schema.promotions (
    id SERIAL PRIMARY KEY,
    discount VARCHAR(50),
    title VARCHAR(100),
    description TEXT,
    image_url VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
