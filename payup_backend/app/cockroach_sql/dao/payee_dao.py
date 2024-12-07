from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from payup_backend.app.cockroach_sql.schemas import ProfilePayeeRelation

from ..schemas import PayeeSchema
from ...modules.payee.model import AddPayeeRequest, PayeeModel


class PayeeRepository:
    """CRUD operations on the payee model"""

    def __init__(self):
        self.repo_schema = PayeeSchema

    async def add_payee(
        self,
        session: AsyncSession,
        user_id: UUID,
        payee: AddPayeeRequest,
        name: str,
        profile_id: UUID,
    ) -> PayeeModel:
        """Add a new payee for a user and link to the profile."""

        # Check if a payee with the same upi_id or account_number exists
        stmt = select(self.repo_schema).filter(
            self.repo_schema.user_id == user_id,
            (self.repo_schema.upi_id == payee.upi_id)
            | (self.repo_schema.account_number == payee.account_number),
        )
        result = await session.execute(stmt)
        existing_payee = result.scalar_one_or_none()

        if existing_payee:
            # Logic for handling existing payee
            raise HTTPException(status_code=400, detail="Payee already exists")

        # Create a new payee
        new_payee = self.repo_schema(
            user_id=user_id,  # type: ignore
            name=name,
            upi_id=payee.upi_id,  # type: ignore
            bank_name=payee.bank_name,  # type: ignore
            ifsc=payee.ifsc,  # type: ignore
            account_number=payee.account_number,  # type: ignore
            phone_number=payee.phone_number,  # type: ignore
        )

        session.add(new_payee)
        await session.flush()  # This gets the primary key of the new payee

        # Now add the relation to ProfilePayeeRelation
        relation = ProfilePayeeRelation(
            payee_id=new_payee.payee_id, profile_id=profile_id  # type: ignore
        )
        session.add(relation)

        await session.refresh(new_payee)
        return PayeeModel(**new_payee.__dict__)

    async def get_payees_by_user(
        self, session: AsyncSession, user_id: UUID
    ) -> list[PayeeModel]:
        """Retrieve all payees for a given user"""
        stmt = select(self.repo_schema).filter(self.repo_schema.user_id == user_id)
        result = await session.execute(stmt)
        db_models = result.scalars().all()
        return [PayeeModel(**db_model.__dict__) for db_model in db_models]

    async def delete_payee(
        self, session: AsyncSession, user_id: UUID, payee_id: UUID, profile_id: UUID
    ):
        """Delete a payee and its relation to a profile for a user."""

        # Check if the payee exists for the user
        stmt = select(self.repo_schema).filter(
            self.repo_schema.user_id == user_id,
            self.repo_schema.payee_id == payee_id,
        )
        result = await session.execute(stmt)
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise HTTPException(status_code=404, detail="Payee not found")

        # Delete the relation between payee and profile in ProfilePayeeRelation
        relation_stmt = select(ProfilePayeeRelation).filter(
            ProfilePayeeRelation.payee_id == payee_id,
            ProfilePayeeRelation.profile_id == profile_id,
        )
        relation_result = await session.execute(relation_stmt)
        relation = relation_result.scalar_one_or_none()

        if relation:
            await session.delete(relation)

        # Check if this payee is linked to any other profiles
        other_relations_stmt = select(ProfilePayeeRelation).filter(
            ProfilePayeeRelation.payee_id == payee_id
        )
        other_relations_result = await session.execute(other_relations_stmt)
        other_relations = other_relations_result.scalars().all()

        # If no other relations exist, delete the payee
        if not other_relations:
            await session.delete(db_model)
