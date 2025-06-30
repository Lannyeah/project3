from fastapi import APIRouter, status, Depends, HTTPException, Query, Body, Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc, asc

from app.database import get_session
from app.models import User, Category, Equipment
from app.schemas import CategoryCreate, CategoryOutSimple, CategoryOutFull, EquipmentOutbyCategory
from app.supfunctions import get_current_admin, get_current_user, sortdict


router = APIRouter()

async def get_category(
        category_id: int = Path(..., description="ID категории"),
        session: AsyncSession = Depends(get_session)
) -> Category:
    category = await session.scalar(
        select(Category)
        .where(Category.id == category_id)
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return category

@router.post(
        '', 
        status_code=status.HTTP_201_CREATED, 
        response_model=CategoryOutSimple,
        summary="Создать новую категорию",
        description="Создание новой категории. Доступно только администраторам",
        responses={
            201: {"description": "Категория успешно создана"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "У вас нет прав администратора"},
            409: {"description": "Категория с таким названием уже существует"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def add_category(
    category_in: CategoryCreate = Body(..., description="Объект новой категории"),
    _current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
) -> CategoryOutSimple:
    category = Category(**category_in.model_dump(exclude_unset=True))
    session.add(category)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    await session.refresh(category)
    return CategoryOutSimple.model_validate(category)

@router.get(
        '', 
        status_code=status.HTTP_200_OK, 
        response_model=list[CategoryOutSimple],
        summary="Вывести список категорий",
        description="Возвращает список по настраиваемым параметрам поиска",
        responses={
            200: {"description": "OK"},
            400: {"description": "Категории могут быть отсортированы только по ID или названию"},
            401: {"description": "Вы не авторизованы"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def get_categories(
    sorted_by: str = Query("title", description="Сортировка по id/title"),
    order: bool = Query(False, description="Сортировка по алфавиту, если title, и по возрастанию, если id - True, обратное - False"),
    limit: int = Query(10, description="Количество выводимых категорий"),
    offset: int = Query(0, description="Пропуск n категорий перед выводом"),
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> list[CategoryOutSimple]:
    if sorted_by not in ("id", "title"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категории могут быть отсортированы только по ID или названию"
        )
    srt = Category.id if sorted_by == "id" else Category.title
    categories = (
        await session.scalars(
            select(Category)
            .order_by(asc(srt) if order else desc(srt))
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [CategoryOutSimple.model_validate(category) for category in categories]

@router.get(
        '/{category_id}', 
        status_code=status.HTTP_200_OK, 
        response_model=CategoryOutFull,
        summary="Поиск категории по ID",
        description="Возвращает категорию с оборудованием по введеному ID категории",
        responses={
            200: {"description": "OK"},
            401: {"description": "Вы не авторизованы"},
            404: {"description": "Категория не найдена"},
            422: {"description": "Ошибка валидации данных"},
        }
)
async def get_category_with_equipment(
    _current_user: User = Depends(get_current_user),
    category: Category = Depends(get_category),
    session: AsyncSession = Depends(get_session)
) -> CategoryOutFull:
    category_full = await session.scalar(
        select(Category)
        .where(Category.id == category.id)
        .options(selectinload(Category.equipment))
    )
    return CategoryOutFull.model_validate(category_full)

@router.get(
        '/{category_id}/', 
        status_code=status.HTTP_200_OK, 
        response_model=list[EquipmentOutbyCategory],
        summary="Вывести список оборудования, входящему в категорию по введенному ID",
        description="Выводит список оборудования, относящийся к категории с введенным ID. Возвращаются объекты оборудования, а не категория",
        responses={
            200: {"description": "OK"},
            400: {"description": "Некорректный параметр сортировки"},
            401: {"description": "Вы не авторизованы"},
            404: {"description": "Категория не найдена"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def get_equipment_by_category(
    sorted_by: str = Query("id", description="Параметр сортировки. id | title | available | owner"),
    order: bool = Query(False, description="Сортировка по алфавиту/по возрастанию - True, обратное - False"),
    limit: int = Query(10, description="Количество выводимых строк оборудования"),
    offset: int = Query(0, description="Пропуск n строк оборудования перед выводом"),
    _current_user: User = Depends(get_current_user),
    category: Category = Depends(get_category),
    session: AsyncSession = Depends(get_session)
) -> list[EquipmentOutbyCategory]:
    if sorted_by not in sortdict.keys() or sorted_by == "category":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оборудование может быть отсортировано только по следующим параметрам: id, title, available, owner"
        )
    equipment_list = (
        await session.scalars(
            select(Equipment)
            .options(selectinload(Equipment.owner))
            .where(Equipment.category_id == category.id)
            .order_by(asc(sortdict[sorted_by]) if order else desc(sortdict[sorted_by]))
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [EquipmentOutbyCategory.model_validate(equipment) for equipment in equipment_list]  

@router.put(
        '/{category_id}', 
        status_code=status.HTTP_200_OK, 
        response_model=CategoryOutSimple,
        summary="Обновить категорию",
        description="Обновляет изменяемые параметры категории. Доступна только администраторам",
        responses={
            200: {"description": "Категория успешно обновлена"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "У вас нет прав администратора"},
            404: {"description": "Категория не найдена"},
            409: {"description": "Категория с таким названием уже существует"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def update_category(
    category_in: CategoryCreate = Body(..., description="Схема изменения категории"),
    _current_admin: User = Depends(get_current_admin),
    category: Category = Depends(get_category),
    session: AsyncSession = Depends(get_session)
) -> CategoryOutSimple:
    for key, value in category_in.model_dump().items():
        setattr(category, key, value)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    await session.refresh(category)
    return CategoryOutSimple.model_validate(category)

@router.delete(
        '/{category_id}', 
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Удалить категорию",
        description="Удаляет категорию. Категорию нельзя удалить, если ей принадлежит хотя бы одно оборудование. Доступно только администраторам",
        responses={
            204: {"description": "Категория успешно удалена"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "У вас нет прав администратора"},
            404: {"description": "Категория не найдена"},
            409: {"description": "Категория не может быть удалена, если к ней относится оборудование"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}            
        }
)
async def delete_category(
    _current_admin: User = Depends(get_current_admin),
    category: Category = Depends(get_category),
    session: AsyncSession = Depends(get_session)
):
    try:
        await session.delete(category)
        await session.commit()
    except:
        await session.rollback()
        raise
    return