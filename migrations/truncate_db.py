import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Database adapter imports
import psycopg2
import psycopg2.extras
import ssl


class CockroachSettings(BaseSettings):
    """creates a singleton constants instance"""

    PASSWORD: str
    USER: str
    CLUSTER: str
    DB: str
    DB_URI: str
    CERT_PATH: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="cockroach_", extra="ignore"
    )


COCKROACH: CockroachSettings = CockroachSettings()

# Base connection string for psycopg2
base_conn_str = f"postgres://{COCKROACH.USER}:{COCKROACH.PASSWORD}@{COCKROACH.DB_URI}/{COCKROACH.DB}"

# SSL context configuration
ssl_context = (
    ssl.create_default_context(cafile=COCKROACH.CERT_PATH)
    if COCKROACH.CERT_PATH
    else None
)
if ssl_context:
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    conn_str = f"{base_conn_str}?sslmode=verify-full&sslrootcert={COCKROACH.CERT_PATH}"
else:
    conn_str = base_conn_str + "?sslmode=disable"

# Connect to the CockroachDB
conn = psycopg2.connect(dsn=conn_str)
conn.set_session(autocommit=False)  # Start a transaction
cursor = conn.cursor()


def main():

    try:
        # Fetch the list of tables
        cursor.execute(
            """
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'dev_schema' AND table_type = 'BASE TABLE';
        """
        )

        tables = cursor.fetchall()

        # Generate and execute TRUNCATE commands
        for schema, table in tables:
            cursor.execute(f"TRUNCATE TABLE {schema}.{table} CASCADE;")

        conn.commit()  # Commit the transaction
        print("All tables truncated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()  # Rollback in case of error
    finally:
        cursor.close()
        conn.close()
