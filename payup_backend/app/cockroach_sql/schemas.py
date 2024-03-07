import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, String, UUID, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

from ..config.constants import get_settings


# Define the base class
class Base(object):
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create the declarative base class
Base = declarative_base(cls=Base)
# Create a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cons = get_settings()
schema = f"{cons.COCKROACH.USER}_schema"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4())
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=False)
    kyc_complete = Column(Boolean, default=False)
    onboarded = Column(Boolean, default=False)

    kycs = relationship(
        "KycEntity",
        back_populates="owner",
    )


class Verifier(Base):
    __tablename__ = "verifiers"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4())
    user_id = Column(UUID, ForeignKey(f"{schema}.users.id"))
    phone_verifier = Column(Integer)
    v_id = Column(String)  # verifier_id
    phone_number = Column(String, unique=True, index=True)
    m_pin = Column(String)
    phone_lock = Column(Boolean, default=False)

    def set_password(self, password):
        """
        Hash the password set by the user at registration.
        """
        self.m_pin = pwd_context.hash(password)

    def get_hash_password(self, password):
        """
        Hash the password set by the user at registration.
        """
        return pwd_context.hash(password)

    def verify_password(self, password):
        """
        Verify the password against the hashed password in the database.
        """
        return pwd_context.verify(password, self.m_pin)


class KycEntity(Base):
    __tablename__ = "kyc_entities"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, index=True, unique=True)
    entity_name = Column(String, nullable=True)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey(f"{schema}.users.id", ondelete="CASCADE")
    )
    verified = Column(Boolean, default=False)
    entity_type = Column(Integer)

    owner = relationship("User", back_populates="kycs")
