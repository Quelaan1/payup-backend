"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
import pytz
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from ...cockroach_sql.database import database
from ...config.constants import get_settings
from .model import (
    TokenBody,
    RefreshTokenUpdate,
    RefreshTokenCreate,
    RefreshToken as RefreshTokenModel,
    AccessTokenBlacklistCreate,
)
from ...models.py_models import BaseResponse
from ...config.errors import NotFoundError
from ...dependency import authentication
from ...cockroach_sql.dao.tokens_dao import RefreshTokenRepo, AccessTokenBlacklistRepo
from ...cockroach_sql.dao.user_dao import UserRepo


logger = logging.getLogger(__name__)

constants = get_settings()


class TokenService:
    """
    The class methods interact with multiple services to facilitate auth endpoints.
    """

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.

        Arguments:
            conn_string {String} -- CockroachDB connection string.
        """
        self.engine = database.engine
        self.sessionmaker = sessionmaker(bind=self.engine)

        self.refresh_token_repo = RefreshTokenRepo()
        self.access_token_repo = AccessTokenBlacklistRepo()
        self.user_repo = UserRepo()
        self.jwt_service = authentication.JWTAuth()

    async def create_new_tokens(self, profile_id: UUID) -> TokenBody:
        """crates a new refresh token"""
        try:
            rt_jti = uuid4()
            now = datetime.utcnow()
            future_time = now + timedelta(minutes=constants.JT.REFRESH_TOKEN_DURATION)

            with self.sessionmaker() as session:
                # query for token number if already exist get if, else create token entity in db
                # get user
                p_user = await self.user_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[(self.user_repo._schema.profile_id, profile_id)],
                )
                rt_model = await self.refresh_token_repo.create_obj(
                    session=session,
                    p_model=RefreshTokenCreate(
                        expires_on=future_time, jti=rt_jti, user_id=p_user[0].id
                    ),
                )
                logger.debug("tokens : %s", rt_model)
                session.commit()

            return await self.get_token_strings(
                profile_id=profile_id, rt_model=rt_model
            )
        except HTTPException as err:
            logger.error("error : %s", err)
            raise err
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(err.args[0]),
            ) from err

    async def refresh_tokens(self, refresh_token_string: str) -> TokenBody:
        """crates a new refresh token"""
        try:
            # put access token in its blacklist if expiry time remains
            # update refresh token in db

            rt_claims_dict = self.jwt_service.decode(refresh_token_string)

            rt_claims_model = authentication.UserRefreshClaim.model_validate(
                rt_claims_dict
            )

            verified = False
            # verify refresh token
            if not verified:
                # delete all tokens for the user
                logger.info("refresh token verification failed")
                return TokenBody(message="invalid token")

            rt_jti = uuid4()
            now = datetime.utcnow()
            future_time = now + timedelta(minutes=constants.JT.REFRESH_TOKEN_DURATION)
            p_model = RefreshTokenUpdate(expires_on=future_time, jti=rt_jti)

            with self.sessionmaker() as session:
                # query for token number if already exist get if, else create token entity in db
                db_users = self.user_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[
                        (self.user_repo._schema.profile_id, rt_claims_model.profile_id)
                    ],
                )
                rt_model = await self.refresh_token_repo.update_obj(
                    session=session,
                    p_model=p_model,
                    obj_id=rt_claims_model.token_family,
                    col_filters=[
                        (self.refresh_token_repo._schema.jti, rt_claims_model.jti),
                        (self.refresh_token_repo._schema.user_id, db_users[0].id),
                    ],
                )
                logger.debug("tokens : %s", rt_model)
                session.commit()

            return await self.get_token_strings(
                profile_id=rt_claims_model.profile_id, rt_model=rt_model
            )

        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args,
            ) from err

    async def get_token_strings(
        self, rt_model: RefreshTokenModel, profile_id: UUID
    ) -> TokenBody:
        """crates a new refresh token"""
        try:
            at_jti = uuid4()
            at_now = datetime.utcnow()
            at_future_time = at_now + timedelta(
                minutes=constants.JT.ACCESS_TOKEN_DURATION
            )
            # int(exp_datetime.timestamp())
            refresh_token_claims = authentication.UserRefreshClaim(
                aud=constants.JT.AUDIENCE,
                exp=int(rt_model.expires_on.timestamp()),
                iat=int(rt_model.updated_at.timestamp()),
                iss=constants.JT.ISSUER,
                sub=str(profile_id),
                profile_id=str(profile_id),
                jti=str(rt_model.jti),
                token_family=str(rt_model.id),
            )

            access_token_claims = authentication.UserAccessClaim(
                aud=constants.JT.AUDIENCE,
                exp=int(at_future_time.timestamp()),
                iat=int(at_now.timestamp()),
                iss=constants.JT.ISSUER,
                sub=str(profile_id),
                profile_id=str(profile_id),
                jti=str(at_jti),
            )

            logger.debug(refresh_token_claims.model_dump())
            logger.debug(access_token_claims.model_dump())

            refresh_token_string = self.jwt_service.encode(
                claims=refresh_token_claims.model_dump()
            )

            access_token_string = self.jwt_service.encode(
                claims=access_token_claims.model_dump()
            )
            return TokenBody(
                access_token=access_token_string, refresh_token=refresh_token_string
            )
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args[0],
            ) from err

    async def handle_signout(self, refresh_token_string: str, access_token_string: str):
        """
        Deletes all refresh_token from db.

        put access_token in blacklist.

        """
        try:
            #
            rt_claims_dict = self.jwt_service.decode(refresh_token_string)

            rt_claims_model = authentication.UserRefreshClaim.model_validate(
                rt_claims_dict
            )

            at_claims_dict = self.jwt_service.decode(access_token_string)

            at_claims_model = authentication.UserAccessClaim.model_validate(
                at_claims_dict
            )

            with self.sessionmaker() as session:
                await self.refresh_token_repo.delete_obj_related_by_profile(
                    session=session, profile_id=rt_claims_model.profile_id
                )

                try:
                    at_model = await self.access_token_repo.create_obj(
                        session=session,
                        p_model=AccessTokenBlacklistCreate(
                            id=at_claims_model.jti,
                            expires_on=datetime.fromtimestamp(
                                at_claims_model.exp, tz=pytz.utc
                            ),
                        ),
                    )
                    session.commit()
                    logger.debug("access token blacklisted : %s", at_model)
                except IntegrityError as e:
                    if "unique constraint" in str(e.orig).lower():
                        logger.info(
                            "Token already blacklisted: %s", at_claims_model.jti
                        )
                        return BaseResponse(message="Already signed out.")
                    raise  # Re-raise if it's not the specific error we're catching

            return BaseResponse(message="Already signed out.")
        except NotFoundError as err:
            raise NotFoundError from err
        except Exception as err:
            logger.error("error : %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err.args[0],
            ) from err
