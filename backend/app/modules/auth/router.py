from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import AuthServiceDep
from app.modules.auth.rate_limit import limit_auth_requests
from app.modules.auth.schemas import (
    AuthResponse,
    Credentials,
    OtpRequest,
    OtpRequestResponse,
    OtpVerify,
)

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(limit_auth_requests)])


@router.post(
    "/otp/request",
    response_model=OtpRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_otp(data: OtpRequest, service: AuthServiceDep) -> OtpRequestResponse:
    return await service.request_otp(data)


@router.post("/otp/verify", response_model=AuthResponse)
async def verify_otp(data: OtpVerify, service: AuthServiceDep) -> AuthResponse:
    return await service.verify_otp(data)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: Credentials, service: AuthServiceDep) -> AuthResponse:
    return await service.register(data)


@router.post("/login", response_model=AuthResponse)
async def login(data: Credentials, service: AuthServiceDep) -> AuthResponse:
    return await service.login(data)
