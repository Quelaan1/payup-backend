"""pan verification service"""

import logging
from fastapi import APIRouter, HTTPException
from starlette import status

from config.constants import ConstantsNamespace
from helperClass.sandbox import Sandbox

from schemas.auth.pan import (
    PANVerifyRequestSchema,
    PANVerifyResponseSchema,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

router = APIRouter()

constants = ConstantsNamespace()
client = Sandbox(constants.SANDBOX_API_KEY, constants.SANDBOX_SECRET_KEY)


@router.post("/auth/verify-pan", response_model=PANVerifyResponseSchema)
async def verify_pan_endpoint(
    pan_verify: PANVerifyRequestSchema,
):
    verification = client.verifyPan(pan_number=pan_verify.pan_number)
    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PAN verification failed",
        )
    if verification.status == 200:
        if verification.Data.Status == "VALID":
            return PANVerifyResponseSchema(message="PAN verified successfully")
        elif verification.status == "INVALID":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PAN verification failed",
            )
