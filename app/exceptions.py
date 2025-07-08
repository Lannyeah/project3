from fastapi import Request, status
from fastapi.responses import JSONResponse


async def handle_integrity_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Некорректная вставка данных в БД"}
    )

async def handle_sqlalchemy_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ошибка сервера"}
    )
