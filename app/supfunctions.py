from fastapi import Cookie, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Equipment, Session, User


async def get_current_user(
        session_id: str = Cookie(None),
        session: AsyncSession = Depends(get_session)
) -> User:
    user = await session.scalar(
        select(User)
        .join(Session, Session.user_id == User.id)
        .where(Session.id == session_id)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Вы не авторизованы"
        )
    return user

async def get_current_admin(
        current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав администратора"
        )
    return current_user

async def get_equipment(
        equipment_id: int = Path(..., description="ID оборудования"),
        session: AsyncSession = Depends(get_session)
) -> Equipment:
    equipment = await session.scalar(
        select(Equipment)
        .where(Equipment.id == equipment_id)
    )
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оборудование не найдено"
        )
    return equipment

async def get_owner(
        equipment: Equipment = Depends(get_equipment),
        current_user: User = Depends(get_current_user)
) -> User:
    if equipment.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не владелец данного оборудования"
        )
    return current_user

sortdict = {
    "id": Equipment.id,
    "title": Equipment.title,
    "available": Equipment.is_available,
    "owner": Equipment.owner_id,
    "category": Equipment.category_id
}
