from typing import Any, Dict, Optional, List, Annotated
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import json
import uuid
from datetime import datetime, timedelta


from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

# Assuming you have similar configurations as in the Go code
SECRET_KEY = "your_jwt_secret_key"
ALGORITHM = "HS256"
ISSUER = "auth@payup.turtlebyte"
AUDIENCE = ["client@payup.turtlebyte", "localhost"]
ACCESS_TOKEN_DURATION = 24 * 60  # in minutes
REFRESH_TOKEN_DURATION = 6 * 30 * 24 * 60  # in minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserClaim(BaseModel):
    profile_id: UUID
    user_id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    browser_info: Optional[str]


class UserAccessClaim(UserClaim):
    iss: str
    sub: str
    aud: list[str]
    exp: int
    iat: int
    jti: str


class UserRefreshClaim(UserClaim):
    iss: str
    sub: str
    aud: list[str]
    exp: int
    iat: int
    jti: str
    token_family: UUID


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
        # except jwt.InvalidAudienceError:
        #     print("Invalid audience")
        # except jwt.InvalidIssuerError:
        #     print("Invalid issuer")
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

    # def authenticate_user(
    #     self, jwt_auth: JWTAuth = Depends(), token: str = Depends(oauth2_scheme)
    # ) -> Dict[str, Any]:
    #     return jwt_auth.decode(token)

    def create_access_token(self, user_claim: UserClaim) -> str:
        claims = UserAccessClaim(aud="asdad")
        return self.encode(claims.model_dump())

    def create_refresh_token(self, claims: UserRefreshClaim) -> str:
        return self.encode(claims.model_dump())


def get_current_active_user():
    pass
