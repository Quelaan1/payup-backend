-- Start a transaction to ensure data integrity
BEGIN;

-- Update the 'profiles' table where conditions are met
UPDATE dev_schema.profiles profiles
SET name = kyc.entity_name
FROM dev_schema.users users
JOIN dev_schema.user_kyc_relations rel ON users.id = rel.user_id
JOIN dev_schema.kyc_entities kyc ON rel.kyc_id = kyc.id
WHERE users.id = profiles.id
AND profiles.name <> kyc.entity_name
AND kyc.entity_type = 2
AND kyc.status = 'VALID';

-- Set name to NULL where no valid kyc_entities are associated
UPDATE dev_schema.profiles profiles
SET name = NULL
WHERE id IN (
    SELECT profiles.id
    FROM dev_schema.profiles
    LEFT JOIN dev_schema.users users ON users.id = profiles.id
    LEFT JOIN dev_schema.user_kyc_relations rel ON users.id = rel.user_id
    LEFT JOIN dev_schema.kyc_entities kyc ON rel.kyc_id = kyc.id
    WHERE (kyc.entity_type = 2 AND kyc.status <> 'VALID' OR kyc.entity_name IS NULL)
);

-- Commit the transaction
COMMIT;
