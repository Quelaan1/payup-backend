import logging
from typing import Union
import httpx
from fastapi import HTTPException, status

from payup_backend.app.cockroach_sql.database import database
from payup_backend.app.cockroach_sql.dao.kyc_dao import KycEntityRepo
from payup_backend.app.cockroach_sql.dao.kyc_lookup_dao import KycLookupRepo
from payup_backend.app.cockroach_sql.db_enums import KycType
from payup_backend.app.modules.kyc.model import KycCreate, KycLookupCreate
from payup_backend.app.utils.encryption_utils import decrypt_entity_id
from .....config.constants import get_settings
from .models import (
    BankVerifyRequest,
    BankVerifyResponse,
    PanVerifyRequest,
    PanVerifyResponse,
    UpiVerifyRequest,
    UpiVerifyResponse,
    AttestError,
)

logger = logging.getLogger(__name__)
constants = get_settings()


class Attestr:
    _base_url = constants.ATTESTR.BASE_URL

    def __init__(self):
        self.sessionmaker = database.get_session()
        self._repo = KycEntityRepo()
        self.lookup_repo = KycLookupRepo()
        self.access_token = constants.ATTESTR.ACCESS_TOKEN

    async def verifyUpi(self, upi_id: str) -> UpiVerifyResponse:
        """Verify UPI VPA and get account holder details."""
        url = f"{self._base_url}/v1/public/finanx/vpa"

        headers = {
            "accept": "application/json",
            "Authorization": f"Basic {self.access_token}",
            "content-type": "application/json",
        }

        request_data = UpiVerifyRequest(vpa=upi_id).model_dump()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=request_data, timeout=20
                )

                logger.info("Status code: %s", response.status_code)

                response.raise_for_status()

                return UpiVerifyResponse.model_validate(response.json())

        except httpx.RequestError as e:
            try:
                error_data = AttestError.model_validate(response.json())
                logger.error("API Error: %s", error_data.message)
                raise HTTPException(
                    detail=error_data.message, status_code=response.status_code
                ) from e
            except Exception:
                raise HTTPException(
                    detail="Failed to process UPI verification",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e

    async def verifyPan(self, pan_number: str) -> Union[KycCreate, PanVerifyResponse]:
        """Verify PAN number."""
        # First, check if PAN already exists and is verified in the lookup table
        async with self.sessionmaker() as session:
            kyc_lookup_list = await self.lookup_repo.get_obj_by_filter(
                session=session,
                col_filters=[
                    (self.lookup_repo.repo_schema.entity_id, pan_number),
                    (self.lookup_repo.repo_schema.entity_type, KycType.PAN.value),
                ],
            )

            if kyc_lookup_list:
                logger.info("PAN %s found in lookup table", pan_number)

                kyc = await self._repo.get_kyc_by_entity_id(
                    session=session,
                    entity_id=pan_number,
                    entity_type=KycType.PAN,
                )

                logger.info("kyc: %s", kyc)

                if kyc.verified:
                    logger.info("PAN %s is already verified", pan_number)

                    pan_verification_response = KycCreate(
                        valid=True,
                        message="PAN already verified",
                        **kyc.model_dump(),
                    )

                    logger.info(
                        "PAN verification response: %s", pan_verification_response
                    )

                    return pan_verification_response
                else:
                    logger.info(
                        "PAN %s found but not verified, proceeding with API verification",
                        pan_number,
                    )
            else:
                logger.info(
                    "PAN %s not found in lookup table, proceeding with API verification",
                    pan_number,
                )

        # If not found or not verified, proceed with API verification
        logger.info("Calling Attestr API for PAN verification")

        url = f"{self._base_url}/v2/public/checkx/pan/comprehensive"

        headers = {
            "accept": "application/json",
            "Authorization": f"Basic {self.access_token}",
            "content-type": "application/json",
        }

        request_data = PanVerifyRequest(pan=pan_number).model_dump()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=request_data, timeout=20
                )

                response.raise_for_status()

                verification = PanVerifyResponse.model_validate(response.json())

                logger.info("Verification result from Attestr: %s", verification)

                if verification.valid and verification.name:
                    logger.info("PAN %s verified successfully", pan_number)

                    # Store verified PAN in KYC tables
                    async with self.sessionmaker() as session:
                        kyc = await self._repo.create_obj(
                            session=session,
                            p_model=KycCreate(
                                entity_id=pan_number,
                                entity_name=verification.name,
                                entity_type=KycType.PAN.value,
                                gender=verification.gender,
                                zip=str(verification.zip),
                                category=verification.category,
                                verified=True,
                                birthorincorporateddate=verification.birthOrIncorporatedDate,
                            ),
                        )

                        await self.lookup_repo.create_obj(
                            session=session,
                            p_model=KycLookupCreate(
                                entity_id=pan_number,
                                entity_type=KycType.PAN.value,
                            ),
                        )
                        await session.commit()

                        logger.info("Stored verified PAN %s in KYC tables", pan_number)

                return PanVerifyResponse.model_validate(response.json())
        except httpx.RequestError as e:
            try:
                error_data = AttestError.model_validate(response.json())

                logger.error("API Error: %s", error_data.message)

                raise HTTPException(
                    detail=error_data.message, status_code=response.status_code
                ) from e
            except Exception:
                raise HTTPException(
                    detail="Failed to process UPI verification",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e

    async def verifyBank(self, account_number: str, ifsc: str) -> BankVerifyResponse:
        """Verify Bank account and IFSC."""
        url = f"{self._base_url}/v1/public/finanx/acc"

        headers = {
            "accept": "application/json",
            "Authorization": f"Basic {self.access_token}",
            "content-type": "application/json",
        }

        request_data = BankVerifyRequest(
            acc=account_number, ifsc=ifsc, fetchIfsc=True
        ).model_dump()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=request_data, timeout=20
                )

                response.raise_for_status()

                return BankVerifyResponse.model_validate(response.json())
        except httpx.RequestError as e:
            try:
                error_data = AttestError.model_validate(response.json())

                logger.error("API Error: %s", error_data.message)

                raise HTTPException(
                    detail=error_data.message, status_code=response.status_code
                ) from e
            except Exception:
                raise HTTPException(
                    detail="Failed to process Bank verification",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e
