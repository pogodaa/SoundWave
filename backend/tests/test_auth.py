import pytest
from httpx import AsyncClient

# === Тесты регистрации ===

class TestRegistration:
    
    async def test_register_success(self, async_client, test_user_data):
        """✅ Успешная регистрация"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_verified"] is False
        assert data["role"] == "unverified"
        assert "id" in data
        assert "created_at" in data
        assert "password_hash" not in data  # Пароль не возвращается!
    
    async def test_register_duplicate_username(self, async_client, test_user_data):
        """❌ Дубликат username → 409"""
        # Первая регистрация
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Вторая с тем же username
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "email": "different@example.com"
            }
        )
        assert response.status_code == 409
        assert "уже существует" in response.json()["detail"]
    
    async def test_register_duplicate_email(self, async_client, test_user_data):
        """❌ Дубликат email → 409"""
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "username": "different_user"
            }
        )
        assert response.status_code == 409
    
    async def test_register_password_too_short(self, async_client, test_user_data):
        """❌ Пароль < 8 символов → 422"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "password": "1234567",  # 7 символов
                "password_confirm": "1234567"
            }
        )
        assert response.status_code == 422
        assert "string_too_short" in str(response.json())
    
    async def test_register_password_too_long(self, async_client, test_user_data):
        """❌ Пароль > 20 символов → 422"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "password": "1" * 21,  # 21 символ
                "password_confirm": "1" * 21
            }
        )
        assert response.status_code == 422
    
    async def test_register_passwords_mismatch(self, async_client, test_user_data):
        """❌ Пароли не совпадают → 422"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "password_confirm": "different_password"
            }
        )
        assert response.status_code == 422
        assert "Пароли не совпадают" in response.json()["detail"]
    
    async def test_register_invalid_email(self, async_client, test_user_data):
        """❌ Неверный формат email → 422"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "email": "not-an-email"
            }
        )
        assert response.status_code == 422
        assert "email" in str(response.json()).lower()
    
    async def test_register_invalid_username(self, async_client, test_user_data):
        """❌ Username с недопустимыми символами → 422"""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                **test_user_data,
                "username": "user@name!"  # недопустимые символы
            }
        )
        assert response.status_code == 422
        assert "string does not match regex" in str(response.json())

# === Тесты логина ===

class TestLogin:
    
    async def test_login_success(self, async_client, test_user_data):
        """✅ Успешный логин"""
        # Сначала регистрируем
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Затем логинимся
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == test_user_data["username"]
    
    async def test_login_wrong_password(self, async_client, test_user_data):
        """❌ Неверный пароль → 401"""
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": test_user_data["username"],
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401
        assert "Неверные учётные данные" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, async_client):
        """❌ Пользователь не найден → 401"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401

# === Тесты защищённых эндпоинтов ===

class TestProtectedEndpoints:
    
    async def test_get_me_with_valid_token(self, async_client, registered_user):
        """✅ GET /users/me с валидным токеном"""
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == registered_user["user"]["username"]
    
    async def test_get_me_without_token(self, async_client):
        """❌ GET /users/me без токена → 401"""
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code == 401
    
    async def test_get_me_with_invalid_token(self, async_client):
        """❌ GET /users/me с невалидным токеном → 401"""
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401

# === Тесты обновления токена ===

class TestTokenRefresh:
    
    async def test_refresh_token_success(self, async_client, registered_user):
        """✅ Обновление access_token"""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": registered_user["refresh_token"]}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    async def test_refresh_with_invalid_token(self, async_client):
        """❌ Неверный refresh_token → 401"""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )
        assert response.status_code == 401