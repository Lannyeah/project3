from io import BytesIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Photo, User
from app.schemas import PhotoOut
from app.supfunctions import get_owner

router = APIRouter()

async def get_photo(
        photo_id: int = Path(..., description="ID фото"),
        session: AsyncSession = Depends(get_session)
) -> Photo:
    photo = await session.scalar(
        select(Photo)
        .where(Photo.id == photo_id)
    )
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фото не найдено"
        )
    return photo

max_size_of_file = 2 * 1024 * 1024
async def upload_photo(
        file: UploadFile = File(..., description="Файл JPEG. Размер файла не должен превышать 2 МБ")
) -> tuple[bytes, str]:
    file_size = 0
    buffer = BytesIO()
    for chunk in iter(lambda: file.file.read(8192), b''):
        file_size += len(chunk)
        if file_size > max_size_of_file:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Размер файла не должен превышать 2 МБ"
            )
        buffer.write(chunk)
    return (buffer.getvalue(), file.filename or "unnamed.jpg") #Добавить логгер на случай отсутствия файлнейма

@router.post(
        '',
        status_code=status.HTTP_201_CREATED,
        response_model=PhotoOut,
        summary="Добавить фото",
        description="Добавляет приложение к оборудованию в формате картинки. Доступно только владельцу оборудования",
        responses={
            204: {"description": "Фото приложено"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование не найдено"},
            409: {"description": "Некорректная вставка данных в БД"},
            413: {"description": "Размер файла не должен превышать 2 МБ"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def add_photo(
    equipment_id: int = Path(..., description="ID оборудования, к которому прилагается новое фото"),
    _owner: User = Depends(get_owner),
    file: tuple[bytes, str] = Depends(upload_photo),
    session: AsyncSession = Depends(get_session)
) -> PhotoOut:
    content, filename = file
    photo = Photo(filename=filename, content=content, equipment_id=equipment_id)
    session.add(photo)
    try:
        await session.commit()
        await session.refresh(photo)
    except:
        await session.rollback()
        raise
    return PhotoOut.model_validate(photo)

@router.get(
        '/{photo_id}',
        response_model=PhotoOut,
        summary="Найти данные приложенного фото по ID",
        description="Выводит данные о приложенной фотографии по ID. Доступно только владельцу оборудования",
        responses={
            200: {"description": "OK"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование/фото не найдены"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def get_photo_info(
    _owner: User = Depends(get_owner),
    photo: Photo = Depends(get_photo)
):
    return PhotoOut.model_validate(photo)

@router.get(
        '/{photo_id}/content',
        status_code=status.HTTP_200_OK,
        summary="Найти изображение по ID",
        description="Выводит для просмотра изображение по ID",
        responses={
            200: {"description": "OK"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование/фото не найдены"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def get_photo_content(
    _owner: User = Depends(get_owner),
    photo: Photo = Depends(get_photo)
):
    return Response(
        content=photo.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{photo.filename}"'}
    )

@router.put(
        '/{photo_id}/content',
        status_code=status.HTTP_200_OK,
        summary="Заменить изображение",
        description="Заменяет изображение и название фото по ID. Доступно только владельцу оборудования",
        responses={
            200: {"description": "Фото успешно изменено"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование/фото не найдены"},
            409: {"description": "Некорректная вставка данных в БД"},
            413: {"description": "Размер файла не должен превышать 2 МБ"},
            422: {"description": "Ошибка валидации данных"},
            500: {"description": "Ошибка со стороны сервера"}
        }
)
async def update_photo(
    _owner: User = Depends(get_owner),
    photo: Photo = Depends(get_photo),
    file: tuple[bytes, str] = Depends(upload_photo),
    session: AsyncSession = Depends(get_session)
):
    content, filename = file
    photo.content = content
    photo.filename = filename
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    await session.refresh(photo)
    return {"Сообщение": "Фото успешно изменено"}

@router.delete(
        '/{photo_id}',
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Удалить фото",
        description="Удалить фото по ID",
        responses={
            204: {"description": "Фото успешно удалено"},
            401: {"description": "Вы не авторизованы"},
            403: {"description": "Вы не владелец данного оборудования"},
            404: {"description": "Оборудование/фото не найдены"},
            422: {"description": "Ошибка валидации данных"}
        }
)
async def delete_photo(
    _owner: User = Depends(get_owner),
    photo: Photo = Depends(get_photo),
    session: AsyncSession = Depends(get_session)
):
    await session.delete(photo)
    try:
        await session.commit()
    except:
        await session.rollback()
        raise
    return
