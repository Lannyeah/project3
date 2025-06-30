from fastapi import APIRouter, status, Depends, HTTPException, Body, Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models import User
from app.schemas import UserOut, PromoteRequest

import bcrypt
import os
from dotenv import load_dotenv


router = APIRouter()

load_dotenv()
root_password = os.getenv("ROOT_PASSWORD")
if not root_password:
    raise RuntimeError("ROOT_PASSWORD is not set in environment")
hashed_root_password = bcrypt.hashpw(root_password.encode(), bcrypt.gensalt())

@router.put(
        '/promote-to-admin/{user_id}', 
        status_code=status.HTTP_200_OK, 
        response_model=UserOut,
        summary="Выдать роль администратора",
        description="Изменяет роль пользователя на администратора. Требуется рут-пароль",
        responses={
            200: {"description": "Новая роль пользователя: администратор"},
            400: {"description": "Некорректный запрос"},
            409: {"description": "Пользователь уже в роли администратора"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def promote_to_admin(
    rootpass: PromoteRequest = Body(..., description="Рут-пароль"),
    user_id: int = Path(..., description="ID пользователя"),
    session: AsyncSession = Depends(get_session)
) -> UserOut:
    user = await session.scalar(
        select(User)
        .where(User.id == user_id)
    )
    if not user or not bcrypt.checkpw(rootpass.password.encode(), hashed_root_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный запрос"
        )
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Данный пользователь уже в роли администратора"
        )
    user.role = "admin"
    try:
        await session.commit()
        await session.refresh(user)
    except:
        await session.rollback()
        raise
    return UserOut.model_validate(user)