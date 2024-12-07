"""layer between router and data access operations. handles db connection, commit, rollback and close."""

import logging
from uuid import UUID
from fastapi import HTTPException, status
from typing import Union
from payup_backend.app.config.errors import NotFoundError
from payup_backend.app.helperClass.verifications.kyc_pan.attestr.attestr import Attestr
from payup_backend.app.helperClass.verifications.kyc_pan.attestr.models import (
    BankVerifyResponse,
    PanVerifyResponse,
)
from payup_backend.app.models.py_models import BaseResponse

from .model import (
    KycCreate,
    KycAadhaarResponse,
    KycLookupCreate,
    KycCreateRequest,
    KycPanVerifyResponse,
    KycUpiVerifyRequest,
    KycUpiVerifyResponse,
)
from ...helperClass.verifications.kyc_pan.sandbox.models import SandboxPANVerifyData
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
from ..profile.model import ProfileUpdate, Profile as ProfileResponse, ProfileWithUserId
from ...helperClass.verifications.kyc_pan.sandbox.sandbox import Sandbox


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
        self.sessionmaker = database.get_session()

        self._repo = KycEntityRepo()
        self.lookup_repo = KycLookupRepo()
        self.relational_repo = UserKycRelationRepo()
        self.profile_repo = ProfileRepo()
        self.user_repo = UserRepo()

        self.sandbox_client = Sandbox(
            constants.SANDBOX.API_KEY, constants.SANDBOX.SECRET_KEY
        )
        self.attestr_client = Attestr()

    # async def pan_verify(
    #     self, profile_id: UUID, pan_id: str, name: str, consent: str, dob: str
    # ) -> Union[KycPanVerifyResponse, None]:
    #     logger.info("checking: PAN %s for profile_id: %s", pan_id, profile_id)

    #     verification = await self.sandbox_client.verifyPan(
    #         pan_data=SandboxPANVerifyData(
    #             consent=consent,
    #             date_of_birth=dob,
    #             name_as_per_pan=name,
    #             pan=pan_id,
    #         )  # type: ignore
    #     )
    #     logger.info(verification)

    #     if verification.Data:
    #         if verification.Data.Status.lower() != "valid":
    #             res = KycResponse(
    #                 entity_id=verification.Data.Pan,
    #                 entity_type=KycType.PAN,
    #                 entity_name=name,
    #                 message=verification.Data.Status,
    #                 date_of_birth_match=verification.Data.MatchDob,
    #                 name_as_per_pan_match=verification.Data.MatchName,
    #             )

    #             raise HTTPException(
    #                 status_code=verification.Code, detail=res.model_dump()
    #             )

    #         if not verification.Data.MatchName or not verification.Data.MatchDob:
    #             # return wrong res
    #             async with self.sessionmaker() as session:
    #                 db_profile = await self.profile_repo.get_obj(
    #                     session=session, obj_id=profile_id
    #                 )
    #                 await session.commit()
    #             res = KycPanVerifyResponse.model_validate(db_profile)
    #             res.date_of_birth_match = verification.Data.MatchDob
    #             res.name_as_per_pan_match = verification.Data.MatchName
    #             res.message = verification.Data.Status
    #             return res

    #         # check data in db and create or retrieve
    #         p_model = KycCreate(
    #             entity_id=verification.Data.Pan,
    #             entity_name=name.upper(),
    #             entity_type=KycType.PAN,
    #             verified=True,
    #             category=verification.Data.Category,
    #             status=verification.Data.Status,
    #         )

    #         async with self.sessionmaker() as session:
    #             kyc_lookup_list = await self.lookup_repo.get_obj_by_filter(
    #                 session=session,
    #                 col_filters=[
    #                     (self.lookup_repo.repo_schema.entity_id, p_model.entity_id),
    #                     (
    #                         self.lookup_repo.repo_schema.entity_type,
    #                         p_model.entity_type.value,
    #                     ),
    #                 ],
    #             )
    #             if len(kyc_lookup_list) == 0:
    #                 logger.info("no entry found for %s", p_model.entity_id)
    #                 kyc = await self._repo.create_obj(session=session, p_model=p_model)
    #                 if p_model.entity_id:
    #                     kyc_lookup = await self.lookup_repo.create_obj(
    #                         session=session,
    #                         p_model=KycLookupCreate(
    #                             entity_id=p_model.entity_id,
    #                             entity_type=p_model.entity_type,
    #                             kyc_entity_id=kyc.id,
    #                         ),
    #                     )
    #             else:
    #                 logger.info("entry found for %s", p_model.entity_id)
    #                 logger.info("# of records found %s", len(kyc_lookup_list))
    #                 kyc = await self._repo.get_obj(
    #                     session=session, obj_id=kyc_lookup_list[0].kyc_entity_id
    #                 )
    #             await session.commit()
    #         logger.info(kyc)

    #         if kyc.entity_name:
    #             db_profile = await self.create_pan_kyc(
    #                 kyc_data=KycCreateRequest(
    #                     entity_id=verification.Data.Pan,
    #                     entity_name=kyc.entity_name,
    #                     entity_type=KycType.PAN,
    #                     internal_id=kyc.id,
    #                 ),
    #                 profile_id=profile_id,
    #             )

    #         res = KycPanVerifyResponse.model_validate(db_profile)
    #         res.date_of_birth_match = verification.Data.MatchDob
    #         res.name_as_per_pan_match = verification.Data.MatchName
    #         res.message = verification.Data.Status
    #         return res

    async def aadhaar_ekyc_otp(
        self,
        profile_id: UUID,
        aadhaar_id: str,
    ):
        try:
            data = AadhaarOtpRequestSchema(aadhaar_number=aadhaar_id)
            logger.info(
                "checking: AADHAAR %s for profile_id: %s", aadhaar_id, profile_id
            )
            ekyc_otp_response = await self.sandbox_client.otpAadhaar(body=data)
            logger.info(ekyc_otp_response)
            if ekyc_otp_response is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AADHAAR ekyc otp failed",
                )
            logger.info(ekyc_otp_response.model_dump())

            if ekyc_otp_response.Data:
                return KycAadhaarResponse(
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
        self, profile_id: UUID, otp: str, ref_id: str, aadhaar_number: str
    ) -> Union[ProfileWithUserId, None]:
        try:
            data = AadhaarVerifyRequestSchema(otp=otp, ref_id=ref_id)
            logger.info(
                "checking: AADHAAR %s for profile_id: %s", data.model_dump(), profile_id
            )
            verification = await self.sandbox_client.verifyAadhaar(body=data)
            if verification is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AADHAAR ekyc otp failed",
                )

            if verification.Data and verification.Data.SplitAddress:
                p_model = KycCreate(
                    entity_id=aadhaar_number,
                    entity_type=KycType.AADHAAR,
                    entity_name=verification.Data.Name,
                    gender=verification.Data.Gender,
                    email=verification.Data.Email,
                    status=verification.Data.Status,
                    zip=verification.Data.SplitAddress.Pincode,
                    verified=True,
                    address=verification.Data.SplitAddress,
                    birthOrIncorporatedDate=verification.Data.DOB,
                )

                async with self.sessionmaker() as session:
                    kyc_lookup_list = await self.lookup_repo.get_obj_by_filter(
                        session=session,
                        col_filters=[
                            (self.lookup_repo.repo_schema.entity_id, p_model.entity_id),
                            (
                                self.lookup_repo.repo_schema.entity_type,
                                p_model.entity_type.value,
                            ),
                        ],
                    )
                    if len(kyc_lookup_list) == 0 and p_model.entity_id:
                        logger.info("no entry found for %s", p_model.entity_id)
                        kyc = await self._repo.create_obj(
                            session=session, p_model=p_model
                        )
                        kyc_lookup = await self.lookup_repo.create_obj(
                            session=session,
                            p_model=KycLookupCreate(
                                entity_id=p_model.entity_id,
                                entity_type=p_model.entity_type,
                            ),
                        )
                    else:
                        logger.info("entry found for %s", p_model.entity_id)
                        logger.info("# of records found %s", len(kyc_lookup_list))
                        kyc_lookup = kyc_lookup_list[0]

                    user_list = await self.user_repo.get_obj_by_filter(
                        session=session,
                        col_filters=[
                            (self.user_repo.repo_schema.profile_id, profile_id)
                        ],
                    )

                    if user_list is None:
                        raise NotFoundError(
                            name=__name__, detail=BaseResponse(message="User not found")
                        )

                    kyc_relation = await self.relational_repo.get_or_create_obj(
                        session=session,
                        user_id=user_list.id,
                    )
                    profile = await self.profile_repo.update_obj(
                        session=session,
                        obj_id=profile_id,
                        p_model=ProfileUpdate(
                            kyc_uidai=True,
                            kyc_complete=True,
                            onboarded=True,
                            name=verification.Data.Name.capitalize(),  # type: ignore
                        ),
                        col_filters=[
                            (self.profile_repo.repo_schema.kyc_pan, True),
                        ],
                    )
                    await session.commit()

                logger.info(profile)
                return ProfileWithUserId(user_id=user_list.id, profile=profile)
        except HTTPException as err:
            raise err
        except Exception as err:
            logger.error(err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err

    async def create_pan_kyc(
        self, kyc_data: KycCreateRequest, profile_id: UUID
    ) -> ProfileWithUserId:
        """validate an access token"""
        try:
            logger.info("attaching: %s", kyc_data.entity_type.name)
            async with self.sessionmaker() as session:
                kyc_lookup_list = await self.lookup_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[
                        (self.lookup_repo.repo_schema.entity_id, kyc_data.entity_id),
                        (
                            self.lookup_repo.repo_schema.entity_type,
                            kyc_data.entity_type.value,
                        ),
                        (
                            self.lookup_repo.repo_schema.id,
                            kyc_data.internal_id,
                        ),
                    ],
                )
                logger.info("here")
                if len(kyc_lookup_list) == 0:
                    logger.info("no entry found for %s", kyc_data.entity_id)
                    raise HTTPException(
                        detail="databse inconsistent",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # create association
                user_list = await self.user_repo.get_obj_by_filter(
                    session=session,
                    col_filters=[(self.user_repo.repo_schema.profile_id, profile_id)],
                )
                if user_list is None:
                    raise NotFoundError(
                        name=__name__, detail=BaseResponse(message="User not found")
                    )
                logger.info("%s", user_list)
                kyc_relation = await self.relational_repo.get_or_create_obj(
                    session=session,
                    kyc_id=kyc_data.internal_id,
                    user_id=user_list.id,
                )
                profile = await self.profile_repo.update_obj(
                    session=session,
                    obj_id=profile_id,
                    p_model=ProfileUpdate(kyc_pan=True),
                )
                await session.commit()

            return ProfileWithUserId(user_id=user_list.id, profile=profile)

        except Exception as err:
            logger.error(err.args)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{err.args}",
            ) from err

    # -----

    async def verify_upi(
        self, req_body: KycUpiVerifyRequest, user_name: str
    ) -> KycUpiVerifyResponse:
        logger.info(
            "checking: UPI %s for profile_id: %s",
            req_body.upi_id,
            user_name,
        )

        verification = await self.attestr_client.verifyUpi(upi_id=req_body.upi_id)

        logger.info("Verification result from sandbox: %s", verification)

        if verification.valid and verification.name:
            return verification
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verification.message,
            )

    async def verify_pan(
        self, pan_number: str, dob: str, name: str, profile_id: UUID, user_id: UUID
    ) -> KycPanVerifyResponse:
        logger.info("Verifying PAN: %s", pan_number)

        verification = await self.attestr_client.verifyPan(pan_number=pan_number)

        valid = getattr(verification, "valid", None)
        verified = getattr(verification, "verified", None)
        name_from_attestr = getattr(verification, "name", None)
        entity_name = getattr(verification, "entity_name", None)
        birthOrIncorporatedDate = getattr(verification, "birthOrIncorporatedDate", None)
        birthOrIncorporatedDate_from_db = getattr(
            verification, "birthorincorporateddate", None
        )

        if (valid or verified) and (name_from_attestr or entity_name):
            name_as_per_pan_match = name_from_attestr == name
            name_as_per_pan_match_from_db = entity_name == name
            date_of_birth_match = birthOrIncorporatedDate == dob
            date_of_birth_match_from_db = birthOrIncorporatedDate_from_db == dob

            if not name_as_per_pan_match and not name_as_per_pan_match_from_db:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Name mismatch",
                )

            if not date_of_birth_match and not date_of_birth_match_from_db:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Date of birth mismatch",
                )

            async with self.sessionmaker() as session:
                profile = await self.profile_repo.get_obj(session, profile_id)
                await session.commit()

            if entity_name:
                return KycPanVerifyResponse(
                    user_id=user_id,
                    profile=profile,
                    name_as_per_pan_match=name_as_per_pan_match_from_db,
                    date_of_birth_match=date_of_birth_match_from_db,
                )
            else:
                return KycPanVerifyResponse(
                    user_id=user_id,
                    profile=profile,
                    name_as_per_pan_match=name_as_per_pan_match,
                    date_of_birth_match=date_of_birth_match,
                )
        else:
            logger.warning(
                "PAN verification failed for %s: %s", pan_number, verification.message
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=verification.message
            )

    async def verify_bank(self, account_number: str, ifsc: str) -> BankVerifyResponse:
        logger.info("checking: BANK %s, %s", account_number, ifsc)

        verification = await self.attestr_client.verifyBank(
            account_number=account_number, ifsc=ifsc
        )

        logger.info("Verification result from sandbox: %s", verification)

        if verification.valid and verification.name:
            return BankVerifyResponse.model_validate(verification)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=verification.message
            )
