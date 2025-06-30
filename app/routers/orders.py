from fastapi import APIRouter, status, Depends, HTTPException, Body, Path, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.database import get_session
from app.models import Order, Equipment, User
from app.schemas import OrderOut, OrderCreate, OrderOutFull
from app.supfunctions import get_current_user


router = APIRouter()

async def get_order(
        order_id: int = Path(..., description="ID заказа"),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
) -> Order:
    order = await session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.equipment))
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    if order.customer_id != user.id and order.equipment.owner_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Заказ недоступен"
        )
    return order

@router.post(
        '', 
        status_code=status.HTTP_201_CREATED, 
        response_model=OrderOut,
        summary="Сделать заказ",
        description="Создает заказ. Нельзя арендовать свое оборудование и оборудование, что уже арендовано",
        responses={
            201: {"description": "Заказ успешно сформирован"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не можете арендовать свое оборудование"},
            404: {"description": "Оборудование не найдено"},
            409: {"description": "Оборудование уже арендовано"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def make_order(
    order_in: OrderCreate = Body(..., description="Схема оформления заказа"),
    user: User = Depends(get_current_user),
    equipment_id: int = Query(..., description="ID оборудования"),
    session: AsyncSession = Depends(get_session)
) -> OrderOut:
    equipment = await session.scalar(
        select(Equipment)
        .where(Equipment.id == equipment_id)
    )
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оборудование не найдено"
        )
    if equipment.owner_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете арендовать свое оборудование"
        )
    if equipment.is_available == False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Оборудование уже арендовано"
        )
    order = Order(
        **order_in.model_dump(exclude_unset=True), 
        customer_id=user.id, 
        equipment_id=equipment.id
    )
    order.total_price = (order.end_date - order.start_date).days * equipment.price_per_day
    session.add(order)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    await session.refresh(order)
    return OrderOut.model_validate(order)

@router.get(
        '', 
        status_code=status.HTTP_200_OK, 
        response_model=list[OrderOutFull],
        summary="Смотреть свои заказы",
        description="Выводит список заказов пользователя",
        responses={
            200: {"description": "OK"},
            401: {"description": "Вы не авторизованы"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def get_orders(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> list[OrderOutFull]:
    orders = (
        await session.scalars(
            select(Order)
            .where(Order.customer_id == user.id)
            .options(selectinload(Order.equipment))
        )
    ).all()
    return [OrderOutFull.model_validate(order) for order in orders]

@router.get(
        '/{order_id}', 
        status_code=status.HTTP_200_OK, 
        response_model=OrderOutFull,
        summary="Найти заказ по ID",
        description="Выводит заказ по введеному ID. Найденный заказ доступен только заказчику, владельцу оборудования и администратору",
        responses={
            200: {"description": "OK"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Заказ недоступен"},
            404: {"description": "Заказ не найден"},
            422: {"description": "Ошибка валидации данных"}
        }      
)
async def get_order_by_id(
    order: Order = Depends(get_order)
) -> OrderOutFull:
    return OrderOutFull.model_validate(order)

@router.delete(
        '/{order_id}', 
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Удалить заказ",
        description="Удаляет заказ по ID. Доступно заказчику",
        responses={
            204: {"description": "Заказ успешно удален"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Заказ недоступен"},
            404: {"description": "Заказ не найден"},
            409: {"description": "Ошибка обновления данных в БД"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def delete_order(
    order: Order = Depends(get_order),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if order.equipment.owner_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Заказ недоступен"
        )
    try:
        await session.delete(order)
        await session.commit()
    except:
        await session.rollback()
        raise
    return