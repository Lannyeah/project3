import pytest

from httpx import AsyncClient
import io

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        '/register',
        json={"username": "Apollo", "password": "suck"}
    )
    await client.post(
        '/register',
        json={"username": "Adminollo", "password": "crack"}
    )
    await client.post(
        '/register',
        json={"username": "Noownerollo", "password": "kick"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_auth_2_n_7(client: AsyncClient):
    response = await client.post(
        '/login',
        json={"username": "Apollo", "password": "suck"}
    )
    assert len(response.cookies) == 1
    response = await client.post('/logout')
    assert len(response.cookies) == 0

@pytest.mark.asyncio
async def test_auth_3(authorized_client: AsyncClient):
    response = await authorized_client.get('/me')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_auth_4(client: AsyncClient):
    response = await client.get('/me')
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_5(client: AsyncClient):
    response = await client.post(
        '/login',
        json={"username": "Apollo", "password": "fuck"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_1(admin_client: AsyncClient):
    response = await admin_client.put(
        '/admin/promote-to-admin/2',
        json={"password": "adminpass"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_admin_2_n_category_1(admin_client: AsyncClient):
    response = await admin_client.post(
        '/categories',
        json={"title": "Секс-игрушки"}
    )
    await admin_client.post(
        '/categories',
        json={"title": "Надувные игрушки"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_admin_3(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/categories',
        json={"title": "Детские игрушки"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_category_2(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/categories'
    )
    data = response.json()
    assert data[0]["title"] == "Секс-игрушки"

@pytest.mark.asyncio
async def test_category_3(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/categories/1'
    )
    data = response.json()
    assert data["title"] == "Секс-игрушки"

@pytest.mark.asyncio
async def test_category_4(admin_client: AsyncClient):
    response = await admin_client.put(
        '/categories/1',
        json={'title': 'Просто игрушки'}
    )
    data = response.json()
    assert data["title"] == "Просто игрушки"

@pytest.mark.asyncio
async def test_category_5(admin_client: AsyncClient):
    response = await admin_client.delete(
        '/categories/1',
    )
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_equipment_1(authorized_client: AsyncClient):
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
async def test_category_6(admin_client: AsyncClient):
    response = await admin_client.delete(
        '/categories/2'
    )
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_equipment_2(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/equipment'
    )
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_equipment_3(authorized_client: AsyncClient):
    response = await authorized_client.get(
        '/equipment/1'
    )
    data = response.json()
    assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_equipment_4(authorized_client: AsyncClient):
    response = await authorized_client.put(
        '/equipment/1',
        json={'price_per_day': 250}
    )
    data = response.json()
    assert data['price_per_day'] == '250.00'

@pytest.mark.asyncio
async def test_equipment_5(authorized_client: AsyncClient):
    response = await authorized_client.delete(
        '/equipment/1'
    )
    assert response.status_code == 204

file = io.BytesIO(b"hahaha")

@pytest.mark.asyncio
async def test_photo_1(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/equipment/2/photos',
        files={"file": ("iluha_mad", file, "image/jpeg")}
    )

    assert response.status_code == 201

@pytest.mark.asyncio
async def test_photo_2(authorized_client: AsyncClient):
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
async def test_photo_3(authorized_client:AsyncClient):
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
async def test_photo_4(authorized_client: AsyncClient):
    response = await authorized_client.delete(
        '/equipment/2/photos/1'
    )
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_photo_5(authorized_client: AsyncClient):
    useless_file = io.BytesIO(b"x" * (2 * 1024 * 1024 + 1))
    response = await authorized_client.post(
        '/equipment/2/photos',
        files={"file": ("my ego", useless_file, "image/jpeg")}
    )
    assert response.status_code == 413

@pytest.mark.asyncio
async def test_order_1(authorized_client_2: AsyncClient):
    response = await authorized_client_2.post(
        '/orders?equipment_id=2',
        json={
            "start_date": "2025-06-17", 
            "end_date": "2025-06-22"
        }
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_order_2(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/orders?equipment_id=3',
        json={
            "start_date": "2025-06-20",
            "end_date": "2025-07-01"
        }
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_order_3(authorized_client_2: AsyncClient):
    response = await authorized_client_2.post(
        '/orders?equipment_id=2',
        json={
            "start_date": "2025-06-17", 
            "end_date": "2025-06-22"
        }        
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_order_4(authorized_client_2: AsyncClient):
    response = await authorized_client_2.get(
        '/orders'
    )
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_order_5(client: AsyncClient):
    await client.post(
        '/register',
        json={"username": "hooba", "password": "booba"}
    )
    await client.post(
        '/login',
        json={"username": "hooba", "password": "booba"}
    )
    response = await client.get(
        '/orders/1'
    )
    await client.get('/logout')
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_order_7(authorized_client: AsyncClient):
    response = await authorized_client.delete(
        '/orders/1'
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_order_6(authorized_client_2: AsyncClient):
    response = await authorized_client_2.delete(
        '/orders/1'
    )
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_valid_data_1(client: AsyncClient):
    response = await client.post(
        '/register',
        json={"username": "  ", "password": "sucker"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_valid_data_2(authorized_client: AsyncClient):
    response = await authorized_client.post(
        '/equipment',
        json={
            "title": "Хехе",
            "description": "Котенок из мемом, ехидно смеющийся",
            "price_per_day": "Математика неспособна отразить всю ценность этой вещи",
            "category_id": 2
        }
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_valid_data_3(client: AsyncClient):
    response = await client.post(
        '/login',
        json={"password": "sucker"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_valid_data_4(authorized_client_2: AsyncClient):
    response = await authorized_client_2.post(
        '/orders?equipment_id=3',
        json={
            "start_date": "2025-06-17",
            "end-date": "2025-06-12"
        }
    )
    assert response.status_code == 422