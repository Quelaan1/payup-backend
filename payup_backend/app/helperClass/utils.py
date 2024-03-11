from google.cloud import secretmanager


def set_db_cert():
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(
        request={"name": "projects/803591674308/secrets/Cockroach_DB/versions/1"}
    )

    payload = response.payload.data.decode("UTF-8")

    print(f"Plaintext: {payload}")

    return payload
