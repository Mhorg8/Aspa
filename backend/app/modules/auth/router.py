from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import AuthServiceDep
from app.modules.auth.rate_limit import limit_auth_requests
from app.modules.auth.schemas import AuthResponse, Credentials

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(limit_auth_requests)])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: Credentials, service: AuthServiceDep) -> AuthResponse:
    return await service.register(data)


@router.post("/login", response_model=AuthResponse)
async def login(data: Credentials, service: AuthServiceDep) -> AuthResponse:
    return await service.login(data)
