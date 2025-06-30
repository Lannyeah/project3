from fastapi import FastAPI

from app.routers import auth, admin, categories, equipment, photos, orders
from app.exceptions import handle_integrity_error, handle_sqlalchemy_error
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dotenv import load_dotenv
import os


load_dotenv()

app: FastAPI = FastAPI(
    title="Project3",
    version="0.2.0",
    debug=os.getenv("DEBUG", "false").lower() == "true"
)

app.include_router(auth.router, tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(categories.router, prefix="/categories", tags=["category"])
app.include_router(equipment.router, prefix="/equipment", tags=["equipment"])
app.include_router(photos.router, prefix="/equipment/{equipment_id}/photos", tags=["equipment"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])

app.add_exception_handler(IntegrityError, handle_integrity_error)
app.add_exception_handler(SQLAlchemyError, handle_sqlalchemy_error)