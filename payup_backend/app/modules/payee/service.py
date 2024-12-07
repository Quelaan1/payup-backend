import logging
from uuid import UUID
from fastapi import HTTPException, status
from payup_backend.app.cockroach_sql.database import database
from payup_backend.app.cockroach_sql.dao.payee_dao import PayeeRepository
from payup_backend.app.helperClass.verifications.kyc_pan.attestr.attestr import Attestr
from payup_backend.app.modules import user
from payup_backend.app.modules.kyc.service import KycService
from payup_backend.app.modules.profile.service import ProfileService
from .model import AddPayeeRequest, PayeeModel
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class PayeeService:
    """
    Handles payee-related operations such as adding, deleting, and fetching payees.
    """

    def __init__(self):
        """
        Establish a connection to the database, creating Engine and Sessionmaker objects.
        """
        self.sessionmaker = database.get_session()
        self.payee_repo = PayeeRepository()
        self.profile_service = ProfileService()
        self.kyc_service = KycService()
        self.attestr_client = Attestr()

    async def add_payee(
        self, user_id: str, payee: AddPayeeRequest, profile_id: str
    ) -> PayeeModel:
        """
        Add a new payee to the user's account.

        Args:
            user_id: The UUID of the user.
            payee: The PayeeModel containing payee details.

        Returns:
            The newly added PayeeModel.
        """

        # async def validate_name_to_pan_name(name: str, pan_number: str):
        #     pan_verification = await self.attestr_client.verifyPan(
        #         pan_number=pan_number
        #     )

        #     valid = getattr(pan_verification, "valid", None)
        #     verified = getattr(pan_verification, "verified", None)
        #     name_from_attestr = getattr(pan_verification, "name", None)
        #     entity_name = getattr(pan_verification, "entity_name", None)

        #     if not valid and not verified:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail="PAN is not valid",
        #         )

        #     if not name_from_attestr and not entity_name:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail="Error in verifying PAN, please try again or contact support",
        #         )

        #     if name_from_attestr is not None:
        #         ratio = fuzz.ratio(name_from_attestr.lower(), name.lower())

        #         logger.info(
        #             "Pan Name to User Name verification: %s, user_name: %s, ratio: %s",
        #             name_from_attestr,
        #             name,
        #             ratio,
        #         )
        #     else:
        #         ratio = fuzz.ratio(entity_name.lower(), name.lower())

        #         logger.info(
        #             "Pan Name to User Name verification: %s, user_name: %s, ratio: %s",
        #             entity_name,
        #             name,
        #             ratio,
        #         )

        #     if ratio < 80:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail="Name mismatch between UPI/Bank and PAN",
        #         )
        #     else:
        #         return pan_verification

        try:
            async with self.sessionmaker() as session:
                async with session.begin():

                    profile = await self.profile_service.get_user_profile(profile_id)

                    if payee.upi_id:
                        upi_verification = await self.kyc_service.verify_upi(
                            payee, profile.name
                        )

                        ratio = fuzz.ratio(
                            upi_verification.name.lower(), profile.name.lower()
                        )

                        logger.info(
                            "UPI Name to User Name verification: %s, user_name: %s, ratio: %s",
                            upi_verification.name,
                            profile.name,
                            ratio,
                        )

                        if ratio > 80:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="You can only transfer to UPI ID which is not registered in your name or your company's name or related parties",
                            )

                        name = upi_verification.name
                        payee.bank_name = upi_verification.bank

                    elif payee.account_number:
                        bank_verification = await self.kyc_service.verify_bank(
                            payee.account_number, payee.ifsc
                        )

                        ratio = fuzz.ratio(
                            bank_verification.name.lower(), profile.name.lower()
                        )

                        logger.info(
                            "Bank Name to User Name verification: %s, user_name: %s, ratio: %s",
                            bank_verification.name,
                            profile.name,
                            ratio,
                        )

                        if ratio > 80:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="You can only transfer to Bank Account which is not registered in your name or your company's name or related parties",
                            )

                        name = bank_verification.name
                        payee.bank_name = bank_verification.ifsc.bank
                        payee.ifsc = bank_verification.ifsc.ifsc

                    new_payee = await self.payee_repo.add_payee(
                        session=session,
                        user_id=UUID(user_id),
                        payee=payee,
                        name=name,
                        profile_id=UUID(profile_id),
                    )

                    await session.commit()
            return new_payee
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("Error adding payee: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not add payee.",
            ) from err

    async def get_payees(self, user_id: str):
        """
        Fetch all payees associated with a user.

        Args:
            user_id: The UUID of the user.

        Returns:
            A list of PayeeModel objects representing the user's payees.
        """
        try:
            async with self.sessionmaker() as session:
                payees = await self.payee_repo.get_payees_by_user(
                    session=session, user_id=UUID(user_id)
                )

                await session.commit()
            return payees
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("Error fetching payees: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not fetch payees.",
            ) from err

    async def delete_payee(self, user_id: str, payee_id: UUID, profile_id: UUID):
        """
        Delete a payee by payee_id for a specific user.

        Args:
            user_id: The UUID of the user.
            payee_id: The UUID of the payee to delete.

        Returns:
            None
        """
        try:
            async with self.sessionmaker() as session:
                async with session.begin():
                    await self.payee_repo.delete_payee(
                        session=session, user_id=user_id, payee_id=payee_id, profile_id=profile_id  # type: ignore
                    )

                    await session.commit()
        except HTTPException as e:
            raise e
        except Exception as err:
            logger.error("Error deleting payee: %s", err)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete payee.",
            ) from err
