from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal
from datetime import datetime, UTC
from typing import Callable

def non_empty_validator(field_name: str) -> Callable[[type[BaseModel], str], str]:
    @field_validator(field_name)
    def validate(cls, v: str) -> str:
        field_title = cls.__pydantic_fields__[field_name].title or field_name
        if not v.strip():
            raise ValueError(f'{field_title} не может быть пустым или состоять из пробелов')
        return v
    return validate

class UserCreate(BaseModel):
    username: str = Field(..., title="Имя пользователя", description="Должно быть заполнено", examples=["John_Doe"])
    password: str = Field(..., title="Пароль", description="Должно быть заполнено")

    _validate_username = non_empty_validator("username")
    _validate_password = non_empty_validator("password")

class PromoteRequest(BaseModel):
    password: str = Field(..., title="Рут-пароль", description="Должно быть заполнено")

    _validate_password = non_empty_validator("password")

class UserOut(BaseModel):
    id: int = Field(..., title="ID пользователя")
    username: str = Field(..., title="Имя пользователя")
    role: str = Field(..., title="Роль пользователя")

    model_config = ConfigDict(from_attributes=True)

class EquipmentCreate(BaseModel):
    title: str = Field(..., title="Наименование", description="Должно быть заполнено", examples=["Кофеварка", "Принтер"])
    description: str = Field(..., title="Описание", description="Должно быть заполнено. Максимальный размер - 1000 знаков.", examples=["Huevo. Кофеварка бла-бла-бла", "Canyon. Принтер HFDFSVFV-3434"])
    price_per_day: Decimal = Field(..., title="Стоимость одного дня аренды", description="Должно быть заполнено. Сумма не должна быть отрицательной", examples=[100.00, 200.00])
    category_id: int = Field(..., title="ID категории", description="Должно быть заполнено. Для определения категории обратитесь к get /categories. Если подходящей категории нет, обратитесь в поддержку", examples=[1, 2])

    _validate_title = non_empty_validator("title")
    _validate_description = non_empty_validator("description")
    
    @field_validator("price_per_day")
    def validate_price_per_day(cls, v: Decimal) -> Decimal:
        field_title = cls.__pydantic_fields__["price_per_day"].title or "price_per_day"
        if v < 0:
            raise ValueError(f"Поле {field_title} не может быть отрицательным")
        return v

class EquipmentUpdate(BaseModel):
    title: str | None = Field(None, title="Наименование", description="Заполнить, чтобы изменить")
    description: str | None = Field(None, title="Описание", description="Заполнить, чтобы изменить")
    price_per_day: Decimal | None = Field(None, title="Стоимость одного дня аренды", description="Заполнить, чтобы изменить")
    category_id: int | None = Field(None, title="ID категории", description="Заполнить, чтобы изменить")

class EquipmentOut(BaseModel):
    id: int = Field(..., title="ID оборудования")
    title: str = Field(..., title="Наименование")
    description: str = Field(..., title="Описание")
    price_per_day: Decimal = Field(..., title="Стоимость одного дня аренды")
    is_available: bool = Field(..., title="В наличии")
    owner_id: int = Field(..., title="ID владельца оборудования")
    category_id: int = Field(..., title="ID категории")

    model_config = ConfigDict(from_attributes=True)

class EquipmentOutbyCategory(BaseModel):
    id: int = Field(..., title="ID оборудования")
    title: str = Field(..., title="Наименование")
    description: str = Field(..., title="Описание")
    price_per_day: Decimal = Field(..., title="Стоимость одного дня аренды")
    is_available: bool = Field(..., title="В наличии")
    owner_id: int = Field(..., title="ID владельца оборудования")

    model_config = ConfigDict(from_attributes=True)

class PhotoOut(BaseModel):
    id: int = Field(..., title="ID фото")
    filename: str = Field(..., title="Название файла")
    equipment_id: int = Field(..., title="ID оборудования", description="Оборудование, к которому приложено фото")

    model_config = ConfigDict(from_attributes=True)

class CategoryCreate(BaseModel):
    title: str = Field(..., title="Название категории", description="Должно быть заполнено", examples=["Электроника", "Бытовая техника"])

    _validate_title = non_empty_validator("title")

class CategoryOutSimple(BaseModel):
    id: int = Field(..., title="ID категории")
    title: str = Field(..., title="Название категории")

    model_config = ConfigDict(from_attributes=True)

class CategoryOutFull(BaseModel):
    id: int = Field(..., title="ID категории")
    title: str = Field(..., title="Название категории")
    equipment: list[EquipmentOutbyCategory] = Field(..., title="Список оборудования", description="Список оборудования, входящего в данную категорию")

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    start_date: datetime = Field(default_factory=lambda: datetime.now(UTC), title="Дата начала аренды", description="Не может быть после или в один день с датой окончания аренды")
    end_date: datetime = Field(..., title="Дата окончания аренды", description="Не может быть до или в один день с началом даты аренды")

    @field_validator("end_date")
    def validate_end_date(cls, end_date, values):
        start_date = values.data.get("start_date")
        if start_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        return end_date
    
class OrderOut(BaseModel):
    id: int = Field(..., title="ID заказа")
    customer_id: int = Field(..., title="ID заказчика")
    equipment_id: int = Field(..., title="ID оборудования")
    start_date: datetime = Field(..., title="Дата начала аренды")
    end_date: datetime = Field(..., title="Дата окончания аренды")
    total_price: Decimal = Field(..., title="Общая стоимость")

    model_config = ConfigDict(from_attributes=True)

class OrderOutFull(BaseModel):
    id: int = Field(..., title="ID заказа")
    start_date: datetime = Field(..., title="Дата начала аренды")
    end_date: datetime = Field(..., title="Дата окончания аренды")
    total_price: Decimal = Field(..., title="Общая стоимость")
    equipment: EquipmentOut = Field(..., title="Арендованное оборудование")

    model_config = ConfigDict(from_attributes=True)