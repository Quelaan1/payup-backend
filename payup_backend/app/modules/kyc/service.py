"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from uuid import UUID
from cryptography.fernet import Fernet
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from .model import (
    KycBase,
    KycResponse,
    KycCreate,
    AadhaarKycResponse,
    KycLookupCreate,
    KycCreateRequest,
    UserKycRelationBase,
)
from ...cockroach_sql.dao.kyc_dao import KycEntityRepo
from ...cockroach_sql.dao.kyc_lookup_dao import KycLookupRepo
from ...cockroach_sql.dao.kyc_user_dao import UserKycRelationRepo
from ...cockroach_sql.dao.profile_dao import ProfileRepo
from ...cockroach_sql.dao.user_dao import UserRepo
from ...cockroach_sql.database import database
from ...cockroach_sql.db_enums import KycType
from ...config.constants import get_settings
from .pan.pan_model import (
    AadhaarVerifyRequestSchema,
    AadhaarOtpRequestSchema,
)
from ..profile.model import ProfileUpdate, Profile as ProfileResponse
from ...helperClass.verifications.kyc_pan.sandbox import Sandbox

# from ...dependency import authentication


logger = logging.getLogger(__name__)

constants = get_settings()


class KycService:
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
        self.sessionmaker = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self._repo = KycEntityRepo()
        self.lookup_repo = KycLookupRepo()
        self.relational_repo = UserKycRelationRepo()
        self.profile_repo = ProfileRepo()
        self.user_repo = UserRepo()

        self.sandbox_client = Sandbox(
            constants.SANDBOX.API_KEY, constants.SANDBOX.SECRET_KEY
        )

    async def get_kyc_entity(self, obj_id: UUID):
        """
        Wraps a `session` call that gets a profile.

        Arguments:
            obj_id {UUID} -- The profile's unique ID.
        """
        async with self.sessionmaker() as session:
            kyc = await self._repo.get_obj(session=session, obj_id=obj_id)
            await session.commit()
        return kyc

    async def filter_kyc_entity(self, entity_id: str, entity_type: KycType):
        """
        Wraps a `session` call that gets a profile.

        Arguments:
            obj_id {UUID} -- The profile's unique ID.
        """
        # encrypt data
        if entity_type == KycType.PAN:
            key = constants.PAYUP.PAN_KEY
        elif entity_type == KycType.AADHAAR:
            key = constants.PAYUP.UIDAI_KEY
        else:
            raise HTTPException(
                detail=f"entity_type : {entity_type.name} has no key set in env",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        coder = Fernet(key)
        encoded_data = coder.encrypt(entity_id.encode())
        async with self.sessionmaker() as session:
            kyc = await self._repo.get_obj_by_filter(
                session=session,
                col_filters=[
                    (self._repo._schema.entity_id, encoded_data),
                    (self._repo._schema.entity_type, entity_type.value),
                ],
            )
            await session.commit()
        return kyc

    # async def update_kyc_entity(self, obj_id: UUID, update_model: ProfileUpdate):
    #     """
    #     Wraps a `session` call that updates kycs in a particular city as a list of dictionaries.

    #     Arguments:
    #         obj_id {UUID} -- The profile's id.
    #         update_model {ProfileUpdate} -- profile's update model

    #     Returns:
    #         List -- A list of dictionaries containing kyc data.
    #     """
    #     async with self.sessionmaker() as session:
    #         kyc = await self._repo.update_obj(
    #             session=session, obj_id=obj_id, p_model=update_model
    #         )
    #         await session.commit()
    #     return kyc

    async def verify_kyc(self, kyc_data: KycBase) -> KycResponse:
        """validate an access token"""
        try:
            if kyc_data.entity_type == KycType.AADHAAR:
                logger.info("checking: %s", kyc_data.entity_type.name)
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="aadhaar not implemented",
                )
            if kyc_data.entity_type == KycType.GSTN:
                logger.info("checking: %s", kyc_data.entity_type.name)
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=f"{kyc_data.entity_type.name} not implemented",
                )
        except Exception as err:
            logger.error(err.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err

    async def pan_verify(
        self,
        owner_id: UUID,
        pan_id: str,
    ):
        try:
            logger.info("checking: PAN %s for profile_id: %s", pan_id, owner_id)
            verification = await self.sandbox_client.verifyPan(pan_number=pan_id)
            logger.info(verification)

            if verification.Data.Status.lower() == "valid":
                # check data in db and create or retrieve
                p_model = KycCreate(
                    entity_id=verification.Data.Pan,
                    entity_name=verification.Data.FullName,
                    entity_type=KycType.PAN,
                    verified=True,
                    category=verification.Data.Category,
                )

                async with self.sessionmaker() as session:
                    kyc_lookup = await self._repo.get_obj_by_filter(
                        session=session,
                        col_filters=[
                            (self.lookup_repo._schema.entity_id, p_model.entity_id),
                            (
                                self.lookup_repo._schema.entity_type,
                                p_model.entity_type.value,
                            ),
                        ],
                    )
                    if len(kyc_lookup) == 0:
                        logger.info("no entry found for %s", p_model.entity_id)
                        kyc = await self._repo.create_obj(
                            session=session, p_model=p_model
                        )
                        kyc_lookup = await self.lookup_repo.create_obj(
                            session=session,
                            p_model=KycLookupCreate(
                                entity_id=p_model.entity_id,
                                entity_type=p_model.entity_type,
                                kyc_entity_id=kyc.id,
                            ),
                        )
                    else:
                        logger.info("entry found for %s", p_model.entity_id)
                        logger.info("# of records found %s", len(kyc_lookup))
                        kyc = await self._repo.get_obj(
                            session=session, obj_id=kyc_lookup[0].id
                        )
                    await session.commit()
                logger.info(kyc)

            return KycResponse(
                entity_id=verification.Data.Pan,
                entity_type=KycType.PAN,
                entity_name=verification.Data.FullName,
                message=verification.Data.Status,
                internal_id=kyc.id,
            )

        except Exception as err:
            logger.error(err.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err

    async def aadhaar_ekyc_otp(
        self,
        owner_id: UUID,
        aadhaar_id: str,
    ):
        try:
            data = AadhaarOtpRequestSchema(aadhaar_number=aadhaar_id)
            logger.info("checking: AADHAAR %s for profile_id: %s", aadhaar_id, owner_id)
            ekyc_otp_response = await self.sandbox_client.otpAadhaar(body=data)
            logger.info(ekyc_otp_response)
            if ekyc_otp_response is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AADHAAR ekyc otp failed",
                )
            logger.info(ekyc_otp_response.model_dump())

            return AadhaarKycResponse(
                ref_id=ekyc_otp_response.Data.RefId,
                message=ekyc_otp_response.Data.Message,
            )
        except Exception as err:
            logger.error(err.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err

    async def aadhaar_ekyc_verify(
        self, owner_id: UUID, otp: str, ref_id: str, aadhaar_number: str
    ):
        try:
            data = AadhaarVerifyRequestSchema(otp=otp, ref_id=ref_id)

            logger.info(
                "checking: AADHAAR %s for profile_id: %s", data.model_dump(), owner_id
            )
            ekyc_verify_response = await self.sandbox_client.verifyAadhaar(body=data)
            logger.info(ekyc_verify_response)
            if ekyc_verify_response is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AADHAAR ekyc otp failed",
                )

            res = KycResponse(
                entity_id=aadhaar_number,
                entity_type=KycType.AADHAAR,
                message=ekyc_verify_response.Data.Message,
                entity_name=ekyc_verify_response.Data.Name,
            )
            logger.info(res)
            return res
        except HTTPException as err:
            raise err
        except Exception as err:
            logger.error(err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err

    async def create_kyc(
        self, kyc_data: KycCreateRequest, profile_id: UUID
    ) -> ProfileResponse:
        """validate an access token"""
        try:
            if kyc_data.entity_type == KycType.PAN:
                logger.info("attaching: %s", kyc_data.entity_type.name)
                async with self.sessionmaker() as session:
                    kyc_lookup = await self.lookup_repo.get_obj_by_filter(
                        session=session,
                        col_filters=[
                            (self.lookup_repo._schema.entity_id, kyc_data.entity_id),
                            (
                                self.lookup_repo._schema.entity_type,
                                kyc_data.entity_type.value,
                            ),
                            (
                                self.lookup_repo._schema.kyc_entity_id,
                                kyc_data.internal_id,
                            ),
                        ],
                    )
                    if len(kyc_lookup) == 0:
                        logger.info("no entry found for %s", kyc_data.entity_id)
                        raise HTTPException(
                            detail="wrong kyc data sent, conflict with stored info",
                            status_code=status.HTTP_400_BAD_REQUEST,
                        )

                    logger.info("entry found for %s", kyc_data.entity_id)
                    logger.info("# of records found %s", len(kyc_lookup))
                    # create association
                    user_list = await self.user_repo.get_obj_by_filter(
                        session=session,
                        col_filters=[(self.user_repo._schema.profile_id, profile_id)],
                    )
                    kyc_relation = await self.relational_repo.get_or_create_obj(
                        session=session,
                        kyc_id=kyc_data.internal_id,
                        user_id=user_list[0].id,
                    )
                    profile = await self.profile_repo.update_obj(
                        session=session,
                        obj_id=profile_id,
                        p_model=ProfileUpdate(kyc_pan=True),
                    )
                    await session.commit()
                logger.info(kyc_relation)
                logger.info(profile)
                return profile
            if kyc_data.entity_type == KycType.AADHAAR:
                logger.info("checking: %s", kyc_data.entity_type.name)
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="aadhaar not implemented",
                )
            # if kyc_data.entity_type == KycType.GSTN:
            logger.info("checking: %s", kyc_data.entity_type.name)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"{kyc_data.entity_type.name} not implemented",
            )

        except Exception as err:
            logger.error(err.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err
