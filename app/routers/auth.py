from fastapi import APIRouter, Depends, Response, HTTPException, status, Cookie, Body

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models import User, Session
from app.schemas import UserOut, UserCreate
from app.supfunctions import get_current_user

import bcrypt
import secrets


router = APIRouter()

@router.post(
        '/register', 
        status_code=status.HTTP_201_CREATED, 
        response_model=UserOut,
        summary="Создать аккаунт",
        description="Создает пользователя",
        responses={
            201: {"description": "Пользователь создан успешно"},
            409: {"description": "Имя пользователя занято"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def register_user(
    user_in: UserCreate = Body(..., description="Объект нового пользователя"),
    session: AsyncSession = Depends(get_session)
) -> UserOut:
    username = user_in.username
    hashed_password = bcrypt.hashpw(user_in.password.encode(), bcrypt.gensalt())
    user = User(username=username, hashed_password=hashed_password)
    session.add(user)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    return UserOut.model_validate(user)

@router.post(
        '/login', 
        status_code=status.HTTP_200_OK,
        summary="Авторизоваться",
        description="Авторизация пользователя",
        responses={
            200: {"description": "Пользователь успешно авторизован"},
            400: {"description": "Пользователь уже авторизован"},
            401: {"description": "Неверно введены имя пользователя или пароль"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def login(
    response: Response,
    user_in: UserCreate = Body(..., description="Форма авторизации"),
    session_id: str = Cookie(None),
    session: AsyncSession = Depends(get_session)
):
    if session_id:
        db_session = await session.scalar(
            select(Session)
            .where(Session.id == session_id)
        )
        if db_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы уже авторизованы"
            )
    user = await session.scalar(
        select(User)
        .where(User.username == user_in.username)
    )
    if not user or not bcrypt.checkpw(user_in.password.encode(), user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверно введены имя пользователя или пароль"
        )
    session_id = secrets.token_hex(32)
    db_session = Session(id=session_id, user_id=user.id)
    session.add(db_session)
    try:
        await session.commit()
    except Exception as e: 
        await session.rollback()
        raise
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "Успешно авторизовано"}

@router.get(
        '/me', 
        status_code=status.HTTP_200_OK, 
        response_model=UserOut,
        summary="Показать мои данные",
        description="Возвращает данные об авторизованном пользователе",
        responses={
            200: {"description": "ОК"},
            401: {"description": "Пользователь не авторизован"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    return UserOut.model_validate(current_user)

@router.delete(
        '/logout',
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Выйти",
        description="Завершение сессии",
        responses={
            204: {"description": "Вы вышли из аккаунта"},
            401: {"description": "Вы не авторизованы"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def logout(
    response: Response,
    _current_user: User = Depends(get_current_user),
    session_id: str = Cookie(...),
    session: AsyncSession = Depends(get_session)
):
    db_session = await session.scalar(
        select(Session)
        .where(Session.id == session_id)
    )
    await session.delete(db_session)
    response.delete_cookie("session_id")
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    return {"message": "Вы вышли из аккаунта"}