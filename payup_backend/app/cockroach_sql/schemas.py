"""Sqlalchemy model for cockroach db tables"""

import uuid
import pytz
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
    UUID,
    Integer,
    DateTime,
    SmallInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

from ..config.constants import get_settings


# Define the base class
class Base(object):
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )


# Create the declarative base class
Base = declarative_base(cls=Base)
# Create a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cons = get_settings()
schema = f"{cons.COCKROACH.USER}_schema"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_type = Column(SmallInteger)
    is_active = Column(Boolean, default=False)
    phone_lock = Column(Boolean, default=False)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey(f"{schema}.profiles.id", ondelete="CASCADE")
    )

    kycs = relationship(
        "KycEntity",
        back_populates="owner",
    )

    phones = relationship(
        "PhoneEntity",
        back_populates="owner",
    )


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    kyc_complete = Column(Boolean, default=False)
    onboarded = Column(Boolean, default=False)


class KycEntity(Base):
    __tablename__ = "kyc_entities"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, index=True, unique=True)
    entity_name = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    entity_type = Column(SmallInteger)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey(f"{schema}.users.id", ondelete="CASCADE")
    )

    owner = relationship("User", back_populates="kycs")


class OtpEntity(Base):
    __tablename__ = "otps"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    m_otp = Column(Integer)
    expires_at = Column(DateTime)  # update on update


class PhoneEntity(Base):
    __tablename__ = "phone_entities"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    m_number = Column(String, index=True, unique=True)
    m_pin = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey(f"{schema}.users.id", ondelete="CASCADE")
    )

    owner = relationship("User", back_populates="phones")

    def set_password(self, password):
        """
        Hash the password set by the user at registration.
        """
        self.m_pin = pwd_context.hash(password)

    @classmethod
    def get_hash_password(cls, password):
        """
        Hash the password set by the user at registration.
        """
        return pwd_context.hash(password)

    def verify_password(self, password):
        """
        Verify the password against the hashed password in the database.
        """
        return pwd_context.verify(password, self.m_pin)


class Item(Base):
    __tablename__ = "item_entities"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String, index=True, unique=True)
    entity_name = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    entity_type = Column(SmallInteger)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey(f"{schema}.users.id", ondelete="CASCADE")
    )


class RefreshTokenEntity(Base):
    """
    Has ttl of 1 month.
    On creating refresh token create or update row for corresponding token family.

    To validate Refresh_token:
        - use "updated_at" == "iat"
        - use "expires_on" == "exp"
        - use "id" == "token_family"

    To Recreate update for "id"=="token_family":
        - "token_id" = "new_jti"
        - "expires_on" = "new_datetime"

    on Signout:
        - delete all tokens for "user_id"

    """

    __tablename__ = "refresh_token_entities"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = Column(UUID, index=True, unique=True)
    expires_on = Column(DateTime)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey(f"{schema}.users.id", ondelete="CASCADE")
    )


class AccessTokenBlacklist(Base):
    """
    Has ttl of 24 Hours.

    Entry for black_listed access_token.

    On SignOut:
        - add access token.

    To validate access_token:
        - check "id"="jti" in this table or not

    """

    __tablename__ = "access_token_blacklists"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expires_on = Column(DateTime)
