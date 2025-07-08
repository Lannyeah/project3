from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Equipment, User
from app.schemas import EquipmentCreate, EquipmentOut, EquipmentUpdate
from app.supfunctions import get_current_user, get_equipment, get_owner, sortdict

router = APIRouter()

@router.post(
        '',
        status_code=status.HTTP_201_CREATED,
        response_model=EquipmentOut,
        summary="Добавить оборудование",
        description="Добавляет оборудование. Оборудование привязывается к авторизованному пользователю",
        responses={
            201: {"description": "Оборудование успешно добавлено"},
            401: {"description": "Вы не авторизованы"},
            409: {"description": "Некорректная вставка данных в БД"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def create_equipment(
    equipment_in: EquipmentCreate = Body(..., description="Объект нового оборудования"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> EquipmentOut:
    equipment = Equipment(
        **equipment_in.model_dump(exclude_unset=True),
        owner_id=current_user.id
        )
    session.add(equipment)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    await session.refresh(equipment)
    return EquipmentOut.model_validate(equipment)

@router.get(
        '',
        status_code=status.HTTP_200_OK,
        response_model=list[EquipmentOut],
        summary="Вывести список оборудования",
        description="Возвращает список оборудования",
        responses={
            200: {"description": "OK"},
            400: {"description": "Оборудование может быть отсортировано только по следующим параметрам: id, title, available, owner, category"},
            401: {"description": "Вы не авторизованы"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def get_list_of_equipment(
    sorted_by: str = Query("id", description="Параметр сортировки. id | title | available | owner | category"),
    order: bool = Query(False, description="Сортировка по алфавиту/по возрастанию - True, обратное - False"),
    limit: int = Query(10, description="Количество выводимых строк оборудования"),
    offset: int = Query(0, description="Пропуск n строк оборудования перед выводом"),
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> list[EquipmentOut]:
    if sorted_by not in sortdict.keys():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оборудование может быть отсортировано только по следующим параметрам: id, title, available, owner, category"
        )
    equipment_list = (
        await session.scalars(
            select(Equipment)
            .order_by(asc(sortdict[sorted_by]) if order else desc(sortdict[sorted_by]))
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [EquipmentOut.model_validate(equipment) for equipment in equipment_list]

@router.get(
        '/{equipment_id}',
        status_code=status.HTTP_200_OK,
        response_model=EquipmentOut,
        summary="Найти оборудование по ID",
        description="Возвращает оборудование по его ID",
        responses={
            200: {"description": "OK"},
            401: {"description": "Вы не авторизованы"},
            404: {"description": "Оборудование не найдено"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def get_equipment_full(
    _current_user: User = Depends(get_current_user),
    equipment: Equipment = Depends(get_equipment),
) -> EquipmentOut:
    return EquipmentOut.model_validate(equipment)

@router.put(
        '/{equipment_id}',
        status_code=status.HTTP_200_OK,
        response_model=EquipmentOut,
        summary="Редактировать данные об оборудовании",
        description="Редактирование данных об оборудовании. Доступно владельцам оборудования",
        responses={
            200: {"description": "Оборудование успешно обновлено"},
            400: {"description": "Для операции нужно изменить минимум 1 параметр"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование не найдено"},
            409: {"description": "Некорректная вставка данных в БД"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def update_equipment(
    equipment_in: EquipmentUpdate = Body(..., description="Схема обновления оборудования"),
    _current_owner: User = Depends(get_owner),
    equipment: Equipment = Depends(get_equipment),
    session: AsyncSession = Depends(get_session)
) -> EquipmentOut:
    updates = equipment_in.model_dump(exclude_unset=True, exclude_none=True).items()
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для операции нужно изменить минимум 1 параметр"
        )
    for key, value in updates:
        setattr(equipment, key, value)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    await session.refresh(equipment)
    return EquipmentOut.model_validate(equipment)

@router.delete(
        '/{equipment_id}',
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Удалить оборудование",
        description="Удаляет оборудование. Доступно владельцам. Оборудование нельзя удалить, если оно в действующем заказе",
        responses={
            204: {"description": "Оборудование успешно удалено"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование не найдено"},
            409: {"description": "Вы не можете удалить арендованное оборудование"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def delete_equipment(
    _current_owner: User = Depends(get_owner),
    equipment: Equipment = Depends(get_equipment),
    session: AsyncSession = Depends(get_session)
):
    if not equipment.is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы не можете удалить арендованное оборудование"
        )
    try:
        await session.delete(equipment)
        await session.commit()
    except:
        await session.rollback()
        raise
    return
