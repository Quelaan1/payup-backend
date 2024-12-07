import hashlib
import logging
from payup_backend.app.modules.profile.model import Profile as ProfileModel
from urllib.parse import urlencode
from fastapi import HTTPException, status
import requests

from payup_backend.app.cockroach_sql.dao.profile_dao import ProfileRepo
from payup_backend.app.cockroach_sql.database import database
from .model import InitiatePaymentResponse
import os
import uuid
import re
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def generate_payment_hash(
    key, txnid, amount, productinfo, firstname, email, salt, udf_params=None
):
    """
    Generates a SHA-512 hash for the payment request.

    :param key: Merchant key (string)
    :param txnid: Transaction ID (string)
    :param amount: Amount (string)
    :param productinfo: Product information (string)
    :param firstname: First name (string)
    :param email: Email address (string)
    :param salt: Merchant salt (string)
    :param udf_params: Dictionary of optional UDF parameters (default: None)
    :return: The generated SHA-512 hash (string)
    """
    # Initialize UDF parameters
    udf_fields = [
        "udf1",
        "udf2",
        "udf3",
        "udf4",
        "udf5",
        "udf6",
        "udf7",
        "udf8",
        "udf9",
        "udf10",
    ]
    udf_values = []

    if udf_params is None:
        udf_params = {}

    # Fill in the UDF values, if provided, or leave them blank
    for field in udf_fields:
        udf_values.append(udf_params.get(field, ""))

    # Create the hash sequence as key|txnid|amount|productinfo|firstname|email|udf1|udf2|...|salt
    hash_sequence = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|{'|'.join(udf_values)}|{salt}"

    # Encode the sequence and generate the SHA-512 hash
    hash_value = hashlib.sha512(hash_sequence.encode("utf-8")).hexdigest()

    return hash_value


def generate_txnid():
    """
    Generates a unique transaction ID that matches the pattern ^[a-zA-Z0-9_\|\-\/]{1,40}$
    """
    # Generate a UUID and remove hyphens
    raw_uuid = uuid.uuid4().hex

    # Create a string of allowed characters
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_|-/"

    # Generate a 40-character string using allowed characters
    txnid = "".join(
        allowed_chars[int(c, 16) % len(allowed_chars)] for c in raw_uuid[:40]
    )

    # Ensure the generated txnid matches the required pattern
    if not re.match(r"^[a-zA-Z0-9_\|\-\/]{1,40}$", txnid):
        raise ValueError("Generated txnid does not match the required pattern")

    return txnid


class EasebuzzService:
    """
    Handles easebuzz-related operations such as fetching access token.
    """

    async def initiate_payment(
        self, token_user, amount, productinfo, payment_mode
    ) -> InitiatePaymentResponse:
        """
        Initiates a payment request to easebuzz.

        Args:
            amount: The amount to be paid.
            productinfo: The product information.

        Returns:
            The response from easebuzz.
        """

        self.sessionmaker = database.get_session()

        self.profile_repo = ProfileRepo()

        try:
            async with self.sessionmaker() as session:
                async with session.begin():
                    profile_id = token_user.profile_id

                    profile: ProfileModel | None = await self.profile_repo.get_obj(
                        session=session, obj_id=profile_id
                    )

                    if profile is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Profile not found",
                        )

                    firstname = profile.name
                    email = profile.email

                    profile = await self.profile_repo.get_obj(
                        session=session, obj_id=profile_id
                    )

                    if profile is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Profile not found",
                        )

                    phone = profile.phone_number

                    await session.commit()

            key = os.getenv("EASEBUZZ_KEY")
            salt = os.getenv("EASEBUZZ_SALT")
            url = os.getenv("EASEBUZZ_URL")
            surl = os.getenv("EASEBUZZ_SURL")
            furl = os.getenv("EASEBUZZ_FURL")

            # Generate txnid
            txnid = generate_txnid()

            # Generate hash
            payment_hash = generate_payment_hash(
                key, txnid, amount, productinfo, firstname, email, salt
            )

            payload = {
                "key": key,
                "txnid": txnid,
                "amount": float(amount),
                "productinfo": productinfo,
                "firstname": firstname,
                "phone": phone,
                "email": email,
                "surl": surl,
                "furl": furl,
                "hash": payment_hash,
                "show_payment_mode": payment_mode,
            }

            encoded_payload = urlencode(payload)

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }

            if url is None:
                raise ValueError("URL cannot be None")
            try:
                response = requests.post(url, data=encoded_payload, headers=headers)

                response.raise_for_status()

                logger.info("Initiate Payment Response: %s", response.json())
            except requests.exceptions.HTTPError as errh:
                logger.error(f"HTTP Error: {errh}")
            except requests.exceptions.ConnectionError as errc:
                logger.error(f"Error Connecting: {errc}")
            except requests.exceptions.Timeout as errt:
                logger.error(f"Timeout Error: {errt}")
            except requests.exceptions.RequestException as err:
                logger.error(f"An Error Occurred: {err}")

            return InitiatePaymentResponse(
                status=response.json()["status"],
                data=response.json()["data"],
                error_desc=response.json().get(
                    "error_desc",
                    None,
                ),
            )
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("Error fetching access token: %s", err)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch access token.",
            ) from err
