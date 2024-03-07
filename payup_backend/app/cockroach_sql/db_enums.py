import enum


class KycType(enum.Enum):
    PAN = 1
    AADHAR = 2
    GSTN = 3


class VerifierType(enum.Enum):
    FIREBASE = 1
    TWILIO = 2


class UserType(enum.Enum):
    USER = 1
    ADMIN = 2


def get_kyc_type_name(kyc_type_value: int):
    """Converts a KYC type integer value to its human-readable form."""
    try:
        return KycType(kyc_type_value).name
    except ValueError:
        return None


def get_kyc_type_from_string(kyc_type_str: str):
    """
    Converts a string input to its corresponding KycType enumeration member.
    Returns None if the string does not match any KycType.
    """
    kyc_type_str = (
        kyc_type_str.lower()
    )  # Ensure the input is lowercase to match the enumeration member names
    try:
        return KycType[kyc_type_str]
    except KeyError:
        return None
