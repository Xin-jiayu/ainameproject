from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from dependencies import get_current_user, get_session
from schemas.user_schemas import UserSchema
from services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.get("/me/entitlements")
async def get_my_entitlements(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await UserService(session=session).get_entitlements(current_user.id)
