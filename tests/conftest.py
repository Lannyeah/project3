import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import app
from app.database import get_session
from app.models import Base
from tests.db_test import Async_Session_Test, engine_test


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_db():
    """Создает таблицы до тестов и удаляет после"""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_session():
    async with Async_Session_Test() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_app(async_session):
    """Переопределяет зависимость get_session на тестовую сессию"""

    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def authorized_client(client: AsyncClient):
    """HTTP-клиент с авторизацией обычного пользователя (регистрация производится в тестах)"""
    await client.post("/login", json={"username": "Apollo", "password": "123"})
    yield client
    await client.post("/logout")


@pytest.fixture
async def authorized_client_2(client: AsyncClient):
    """HTTP-клиент с авторизацией невладельца (регистрация производится в тестах)"""
    await client.post("/login", json={"username": "Noownerollo", "password": "789"})
    yield client
    await client.post("/logout")


@pytest.fixture
async def admin_client(client: AsyncClient):
    """HTTP-клиент с авторизацией администратора (регистрация и промоут в тестах)"""
    await client.post("/login", json={"username": "Adminollo", "password": "456"})
    yield client
    await client.post("/logout")
