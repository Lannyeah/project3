import io
import os

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient


#Тесты auth.py
@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        '/register',
        json={"username": "Apollo", "password": "123"}
    )
    await client.post(
        '/register',
        json={"username": "Adminollo", "password": "456"}
    )
    await client.post(
        '/register',
        json={"username": "Noownerollo", "password": "789"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_login_n_logout(client: AsyncClient):
    response = await client.post(
        '/login',
        json={"username": "Apollo", "password": "123"}
    )
    assert len(response.cookies) == 1
    response = await client.post('/logout')
    assert len(response.cookies) == 0

@pytest.mark.asyncio
async def test_me(authorized_client: AsyncClient):
    response = await authorized_client.get('/me')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_unauthorized_me(client: AsyncClient):
    response = await client.get('/me')
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_password(client: AsyncClient):
    response = await client.post(
        '/login',
        json={"username": "Apollo", "password": "000"}
    )
    assert response.status_code == 401

# Тесты admin.py
load_dotenv()
root_pass = os.getenv("ROOT_PASSWORD")
@pytest.mark.asyncio
async def test_promote_to_admin(admin_client: AsyncClient):
    response = await admin_client.put(
        '/admin/promote-to-admin/2',
        json={"password": root_pass}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_add_category_from_admin(admin_client: AsyncClient):
    response = await admin_client.post(
        '/categories',
        json={"title": "Бытовые приборы"}
    )
    await admin_client.post(
        '/categories',
        json={"title": "Надувные игрушки"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_add_category_from_user(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/categories',
        json={"title": "Детские игрушки"}
    )
    assert response.status_code == 403

#Тесты categories.py
@pytest.mark.asyncio
async def test_get_categories(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/categories'
    )
    data = response.json()
    assert data[0]["title"] == "Надувные игрушки"

@pytest.mark.asyncio
async def test_get_category(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/categories/1'
    )
    data = response.json()
    assert data["title"] == "Бытовые приборы"

@pytest.mark.asyncio
async def test_update_category(admin_client: AsyncClient):
    response = await admin_client.put(
        '/categories/1',
        json={'title': 'Просто игрушки'}
    )
    data = response.json()
    assert data["title"] == "Просто игрушки"

@pytest.mark.asyncio
async def test_delete_category(admin_client: AsyncClient):
    response = await admin_client.delete(
        '/categories/1',
    )
    assert response.status_code == 204

#Тесты equipment.py
@pytest.mark.asyncio
async def test_add_equipment(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/equipment',
        json={
            'title': 'Пикачу',
            'description': 'Надувная игрушка Пикачу. Веселая.',
            'price_per_day': 100,
            'category_id': 2
        }
    )
    response = await authorized_client.post(
        '/equipment',
        json={
            'title': 'Надувная дакимакура',
            'description': 'С изображением Ильи Мэддисона',
            'price_per_day': 1000,
            'category_id': 2
        }
    )
    response = await authorized_client.post(
        '/equipment',
        json={
            'title': 'Атомная бомба',
            'description': 'Плюшевая ядерная боеголовка для патриотов',
            'price_per_day': 20,
            'category_id': 2
        }
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_delete_category_with_equipment(admin_client: AsyncClient):
    response = await admin_client.delete(
        '/categories/2'
    )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_get_list_of_equipment(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/equipment'
    )
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_equipment(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/equipment/1'
    )
    data = response.json()
    assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_update_equipment(authorized_client: AsyncClient):
    response = await authorized_client.put(
        '/equipment/1',
        json={'price_per_day': 250}
    )
    data = response.json()
    assert data['price_per_day'] == '250.00'

@pytest.mark.asyncio
async def test_delete_equipment(authorized_client: AsyncClient):
    response = await authorized_client.delete(
        '/equipment/1'
    )
    assert response.status_code == 204

#Тесты photos.py
file = io.BytesIO(b"image")

@pytest.mark.asyncio
async def test_add_photo(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/equipment/2/photos',
        files={"file": ("iluha_mad", file, "image/jpeg")}
    )

    assert response.status_code == 201

@pytest.mark.asyncio
async def test_get_photo(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/equipment/2/photos/1'
    )
    info = response.json()
    assert info["filename"] == "iluha_mad"
    response = await authorized_client.get(
        '/equipment/2/photos/1/content'
    )
    assert response.content == file.getvalue()

@pytest.mark.asyncio
async def test_update_photo(authorized_client:AsyncClient):
    new_file = io.BytesIO(b"haha")
    await authorized_client.put(
        '/equipment/2/photos/1/content',
        files={"file": ("new_iluha_mad", new_file, "image/jpeg")}
    )
    response = await authorized_client.get(
        '/equipment/2/photos/1/content'
    )
    assert response.content == new_file.getvalue()

@pytest.mark.asyncio
async def test_delete_photo(authorized_client: AsyncClient):
    response = await authorized_client.delete(
        '/equipment/2/photos/1'
    )
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_add_photo_with_bigsize(authorized_client: AsyncClient):
    useless_file = io.BytesIO(b"x" * (2 * 1024 * 1024 + 1))
    response = await authorized_client.post(
        '/equipment/2/photos',
        files={"file": ("my ego", useless_file, "image/jpeg")}
    )
    assert response.status_code == 413

#Тесты orders.py
@pytest.mark.asyncio
async def test_add_order(authorized_client_2: AsyncClient):
    response = await authorized_client_2.post(
        '/orders?equipment_id=2',
        json={
            "start_date": "2025-06-17",
            "end_date": "2025-06-22"
        }
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_add_order_own_equipment(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/orders?equipment_id=3',
        json={
            "start_date": "2025-06-20",
            "end_date": "2025-07-01"
        }
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_orders(authorized_client_2: AsyncClient):
    response = await authorized_client_2.get(
        '/orders'
    )
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_orders_from_noncustomer(client: AsyncClient):
    await client.post(
        '/register',
        json={"username": "Alex", "password": "134"}
    )
    await client.post(
        '/login',
        json={"username": "Alex", "password": "134"}
    )
    response = await client.get(
        '/orders/1'
    )
    await client.get('/logout')
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_order_from_noncustomer(authorized_client: AsyncClient):
    response = await authorized_client.delete(
        '/orders/1'
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_order(authorized_client_2: AsyncClient):
    response = await authorized_client_2.delete(
        '/orders/1'
    )
    assert response.status_code == 204

#Тесты валидации pydantic
@pytest.mark.asyncio
async def test_non_empty_data(client: AsyncClient):
    response = await client.post(
        '/register',
        json={"username": "  ", "password": "?"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_type_exception(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/equipment',
        json={
            "title": "Хехе",
            "description": "Котенок из мемов, ехидно смеющийся",
            "price_per_day": "Математика неспособна отразить всю ценность этой вещи",
            "category_id": 2
        }
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_incomplete_response(client: AsyncClient):
    response = await client.post(
        '/login',
        json={"password": "134"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_end_date_validate(authorized_client_2: AsyncClient):
    response = await authorized_client_2.post(
        '/orders?equipment_id=3',
        json={
            "start_date": "2025-06-17",
            "end-date": "2025-06-12"
        }
    )
    assert response.status_code == 422
