"""class interface to interact with firebase services."""

import logging
from fastapi import HTTPException, status
from firebase_admin import auth, initialize_app


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(lineno)d | %(filename)s : %(message)s",
)
logger = logging.getLogger(__name__)

# constants = get_settings()


class FirebaseService:
    """
    The class methods interact with firebase endpoints.
    """

    _instance = None

    @classmethod
    def get_instance(cls):
        """
        Get the instance of FirebaseService.
        """
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the Firebase client.
        """
        # cred = credentials.Certificate("path/to/serviceAccountKey.json")
        self.auth = auth
        self.admin = initialize_app()

    def __init__(self):
        """
        Prevent direct instantiation.
        """
        if FirebaseService._instance is not None:
            raise Exception("This class is a singleton!")

        FirebaseService._instance = self
        self.auth = None
        self.admin = None

    async def verify_id_token(self, id_token: str) -> dict:
        """verify and get id_token detail for token from clients"""
        try:
            decoded_token = self.auth.verify_id_token(id_token)
            logger.info("firebase decoded user info : %s", decoded_token)
            return decoded_token
        except (
            ValueError,
            auth.InvalidIdTokenError,
            auth.ExpiredIdTokenError,
            auth.RevokedIdTokenError,
            auth.UserDisabledError,
        ) as e:
            logger.error(e.args)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"wrong or missing id token : {e.args}",
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{e.args}",
            ) from e

    async def delete_user_account(self, firebase_uid: str):
        """removes user account from the firebase app"""
        try:
            self.auth.delete_user(uid=firebase_uid)
            logger.info("successfully removed user from firebase_aapp")
        except Exception as e:
            logger.error(e.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="internal error",
            ) from e
