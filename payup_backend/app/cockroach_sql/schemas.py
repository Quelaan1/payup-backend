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
    BINARY,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
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

    # Define the relationship to Profile to access phone_number
    profile = relationship("Profile", back_populates="users")

    # Define the relationship to KycEntity through the association table
    kyc_entities = relationship("UserKycRelation", back_populates="users")


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String)
    kyc_complete = Column(Boolean, default=False)
    kyc_pan = Column(Boolean, default=False)
    kyc_uidai = Column(Boolean, default=False)
    onboarded = Column(Boolean, default=False)

    payee_entities = relationship("ProfilePayeeRelation", back_populates="profiles")

    # Add the relationship to User
    users = relationship("User", back_populates="profile")


class KycEntity(Base):
    __tablename__ = "kyc_entities"
    __table_args__ = {"schema": schema}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id_encrypted = Column(String, index=True, unique=True)
    entity_name = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    entity_type = Column(SmallInteger)
    email = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    birthorincorporateddate = Column(String, nullable=True)
    zip = Column(String, nullable=True)
    category = Column(String, nullable=True)
    address = Column(JSONB, nullable=True)
    status = Column(String)

    # Define the relationship to User through the association table
    users = relationship("UserKycRelation", back_populates="kyc_entities")


# Association table for the many-to-many relationship
class UserKycRelation(Base):
    __tablename__ = "user_kyc_relations"
    __table_args__ = {"schema": schema}

    kyc_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{schema}.kyc_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{schema}.users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    users = relationship("User", back_populates="kyc_entities")
    kyc_entities = relationship("KycEntity", back_populates="users")


class KycLookup(Base):
    __tablename__ = "kyc_lookups"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    entity_type = Column(SmallInteger)
    entity_id = Column(String, index=True, unique=True)


class PayeeSchema(Base):
    __tablename__ = "payees"
    __table_args__ = {"schema": schema}

    payee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{schema}.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    upi_id = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    ifsc = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    last_paid = Column(DateTime, nullable=True)
    phone_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )

    profile_payee_relations = relationship(
        "ProfilePayeeRelation", back_populates="payee_entities"
    )


# Association table for the many-to-many relationship
class ProfilePayeeRelation(Base):
    __tablename__ = "profile_payee_relations"
    __table_args__ = {"schema": schema}

    payee_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{schema}.payees.payee_id", ondelete="CASCADE"),
        primary_key=True,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{schema}.profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    profiles = relationship("Profile", back_populates="payee_entities")
    payee_entities = relationship(
        "PayeeSchema", back_populates="profile_payee_relations"
    )


class OtpEntity(Base):
    __tablename__ = "otps"
    __table_args__ = {"schema": schema}

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    m_otp = Column(Integer)
    attempt_remains = Column(Integer)
    expires_at = Column(DateTime)  # update on update


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


class PromotionSchema(Base):
    __tablename__ = "promotions"
    __table_args__ = {"schema": schema}

    id = Column(Integer, primary_key=True)
    discount = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )


class NotificationPreferenceSchema(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = {"schema": "dev_schema"}

    preference_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID, ForeignKey("dev_schema.users.id", ondelete="CASCADE"), nullable=False
    )
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )


class DeviceSchema(Base):
    __tablename__ = "devices"
    __table_args__ = {"schema": schema}
    device_id = Column(String, primary_key=True)
    user_id = Column(
        UUID, ForeignKey(f"{schema}.users.id", ondelete="CASCADE"), nullable=False
    )
    device_type = Column(String, nullable=False)
    last_used = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )


class DeviceTokenSchema(Base):
    __tablename__ = "device_tokens"
    __table_args__ = {"schema": schema}
    token_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    device_id = Column(
        String,
        ForeignKey(f"{schema}.devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String, nullable=False, unique=True)
    token_purpose = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )


class NotificationSchema(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": schema}
    notification_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID, ForeignKey(f"{schema}.users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)
    type = Column(String, nullable=False)
    method = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=datetime.now(pytz.UTC).replace(tzinfo=None),
        onupdate=datetime.now(pytz.UTC).replace(tzinfo=None),
    )
