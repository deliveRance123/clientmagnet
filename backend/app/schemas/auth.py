from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    otp: Optional[str] = Field(None, max_length=10)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class GoogleAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


class GoogleAuthRequest(BaseModel):
    code: Optional[str] = None
    state: Optional[str] = None
    redirect_uri: Optional[str] = None
    id_token: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: Optional[str] = Field("registration", description="registration, login, password_reset, verification")


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)
    purpose: Optional[str] = Field("registration", description="registration, login, password_reset, verification")


class LoginOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)
    new_password: str = Field(..., min_length=8, max_length=128)


class OTPResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: Optional[int] = 600
