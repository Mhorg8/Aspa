import re
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, EmailStr, Field

from app.modules.users.schemas import UserResponse


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


_DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_iranian_phone_number(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Phone number must be a string")
    phone = re.sub(r"[\s()-]", "", value.translate(_DIGIT_TRANSLATION))
    if phone.startswith("0098"):
        phone = "+98" + phone[4:]
    elif phone.startswith("98"):
        phone = "+" + phone
    elif phone.startswith("09"):
        phone = "+98" + phone[1:]
    if not re.fullmatch(r"\+989\d{9}", phone):
        raise ValueError("Enter a valid Iranian mobile number")
    return phone


IranianPhoneNumber = Annotated[str, BeforeValidator(normalize_iranian_phone_number)]


class OtpRequest(BaseModel):
    phone_number: IranianPhoneNumber


class OtpVerify(OtpRequest):
    code: str = Field(pattern=r"^\d{6}$")


class OtpRequestResponse(BaseModel):
    message: str = "If the number can receive messages, an OTP has been sent"
    expires_in: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    user: UserResponse
