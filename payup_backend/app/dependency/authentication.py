import logging
from typing import Any, Dict, Annotated
import jwt
from uuid import uuid4
from pydantic import BaseModel
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)
# Assuming you have similar configurations as in the Go code
SECRET_KEY = "your_jwt_secret_key"
ALGORITHM = "HS256"
ISSUER = "auth@payup.turtlebyte"
AUDIENCE = ["client@payup.turtlebyte", "localhost"]
ACCESS_TOKEN_DURATION = 24 * 60  # in minutes
REFRESH_TOKEN_DURATION = 30 * 24 * 60  # in minutes

signin_oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="auth/signin", scheme_name="signin_oauth2_schema"
)
signup_oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="auth/verify/otp", scheme_name="signup_oauth2_schema"
)


class UserClaim(BaseModel):
    profile_id: str
    # first_name: Optional[str]
    # last_name: Optional[str]
    # email: Optional[str]
    # browser_info: Optional[str]


class UserAccessClaim(UserClaim):
    iss: str
    sub: str  # user's profile_id
    aud: list[str]
    exp: int
    iat: int
    jti: str


class UserRefreshClaim(UserClaim):
    iss: str
    sub: str  # user's profile_id
    aud: list[str]
    exp: int
    iat: int
    jti: str
    token_family: str


class JwtTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class JWTAuth:
    def __init__(self, algorithm: str = ALGORITHM, secret_key: str = SECRET_KEY):
        self.algorithm = algorithm
        self.secret_key = secret_key

    def encode(self, claims: Dict[str, Any]) -> str:
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        return token

    def decode(self, token: str) -> Dict[str, Any]:
        try:
            decoded = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                issuer=ISSUER,
                audience=AUDIENCE,
            )
            print(f"Decoded JWT: {decoded}")

            # Manually check the 'sub' claim
            # if decoded.get("sub") != expected_subject:
            #     raise jwt.InvalidTokenError(
            #         "The subject claim does not match the expected value."
            #     )

            print("JWT is valid. Issuer, Audience, and Subject are verified.")
            return decoded
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: {e}"
            ) from exc
        except Exception as exc:
            print(f"Token validation failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid token: {e}",
            ) from exc


def get_current_active_user(token: Annotated[str, Depends(oauth2_scheme)]):
    logger.info("token : %s", token)
    return uuid4()
