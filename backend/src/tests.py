import os
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.update(
    {
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "test",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "SECRET_KEY": "super-extra-ultra-long-secret-key-for-test-32-chars",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "BACKEND_HOST": "localhost",
        "BACKEND_PORT": "8000",
        "FRONTEND_HOST": "localhost",
        "FRONTEND_PORT": "3000",
        "DEBUG": "True",
    }
)

from src.database import Base, get_db
from src.main import app

# CONFIGURATION

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


# FIXTURES


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_token(client: AsyncClient) -> str:
    user_data = {"username": f"user_{uuid.uuid4().hex[:8]}", "password": "password123"}
    response = await client.post("/api/v1/register", json=user_data)
    return str(response.json()["access_token"])


# TESTS

# Auth & Users


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient) -> None:
    # Успех
    reg_data = {"username": "new_user", "password": "safe_password"}
    res = await client.post("/api/v1/register", json=reg_data)
    assert res.status_code == 201

    # Ошибка: Дубликат (400)
    res_dub = await client.post("/api/v1/register", json=reg_data)
    assert res_dub.status_code == 400

    # Граница: Короткий пароль (422)
    res_short = await client.post(
        "/api/v1/register",
        json={"username": "a", "password": "1"},
    )
    assert res_short.status_code == 422


@pytest.mark.asyncio
async def test_change_username_flow(client: AsyncClient, test_user_token: str) -> None:
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Успех
    new_name = "legit_name"
    res = await client.patch(
        f"/api/v1/users/me?new_username={new_name}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["username"] == new_name

    # Ошибка: Без токена (401)
    res_401 = await client.patch("/api/v1/users/me?new_username=fail")
    assert res_401.status_code == 401


# Posts


@pytest.mark.asyncio
async def test_post_creation_limits(client: AsyncClient, test_user_token: str) -> None:
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Успех
    valid_data = {"title": "Valid Title", "body": "Content longer than 10 chars"}
    res = await client.post("/api/v1/posts", json=valid_data, headers=headers)
    assert res.status_code == 201

    # Граница: Слишком короткое тело (422)
    short_data = {"title": "Title", "body": "short"}
    res_422 = await client.post("/api/v1/posts", json=short_data, headers=headers)
    assert res_422.status_code == 422


@pytest.mark.asyncio
async def test_post_access_and_delete(
    client: AsyncClient,
    test_user_token: str,
) -> None:
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Создание
    post_res = await client.post(
        "/api/v1/posts",
        json={"title": "Delete Me", "body": "Some long enough content"},
        headers=headers,
    )
    post_id = post_res.json()["id"]

    # Успех: Удаление
    del_res = await client.delete(f"/api/v1/posts/{post_id}", headers=headers)
    assert del_res.status_code == 204

    # Ошибка: Повторное удаление/поиск (404)
    get_res = await client.get(f"/api/v1/posts/{post_id}")
    assert get_res.status_code == 404

    # Ошибка: Удаление несуществующего (404)
    fake_id = uuid.uuid4()
    del_404 = await client.delete(f"/api/v1/posts/{fake_id}", headers=headers)
    assert del_404.status_code == 404


@pytest.mark.asyncio
async def test_post_permissions(client: AsyncClient, test_user_token: str) -> None:
    # Юзер 1 создает пост
    headers_1 = {"Authorization": f"Bearer {test_user_token}"}
    post = await client.post(
        "/api/v1/posts",
        json={"title": "Owner Post", "body": "Content content content"},
        headers=headers_1,
    )
    post_id = post.json()["id"]

    # Юзер 2 пытается удалить (403)
    user2_data = {"username": "thief", "password": "password123"}
    reg2 = await client.post("/api/v1/register", json=user2_data)
    token2 = reg2.json()["access_token"]
    headers_2 = {"Authorization": f"Bearer {token2}"}

    res_403 = await client.delete(f"/api/v1/posts/{post_id}", headers=headers_2)
    assert res_403.status_code == 403


@pytest.mark.asyncio
async def test_draft_visibility_flow(client: AsyncClient, test_user_token: str) -> None:
    headers_owner = {"Authorization": f"Bearer {test_user_token}"}

    # Создание черновика
    post_data = {
        "title": "Draft Post",
        "body": "This is a private draft content",
        "is_published": False,
    }
    res = await client.post("/api/v1/posts", json=post_data, headers=headers_owner)
    post_id = res.json()["id"]

    # Успех: Автор видит свой черновик
    res_owner = await client.get(f"/api/v1/posts/{post_id}", headers=headers_owner)
    assert res_owner.status_code == 200

    # Ошибка: Аноним не видит черновик (404)
    res_anon = await client.get(f"/api/v1/posts/{post_id}")
    assert res_anon.status_code == 404

    # Ошибка: Другой юзер не видит черновик (404)
    other_user = {"username": "other", "password": "password123"}
    reg_other = await client.post("/api/v1/register", json=other_user)
    headers_other = {"Authorization": f"Bearer {reg_other.json()['access_token']}"}

    res_other = await client.get(f"/api/v1/posts/{post_id}", headers=headers_other)
    assert res_other.status_code == 404


@pytest.mark.asyncio
async def test_public_posts_listing(client: AsyncClient, test_user_token: str) -> None:
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Создаем публичного и скрытого постов
    await client.post(
        "/api/v1/posts",
        headers=headers,
        json={"title": "Public", "body": "Public content", "is_published": True},
    )
    await client.post(
        "/api/v1/posts",
        headers=headers,
        json={"title": "Private", "body": "Private content", "is_published": False},
    )

    # Проверка общего списка
    res_all = await client.get("/api/v1/posts")
    posts = res_all.json()
    assert len(posts) == 1
    assert posts[0]["is_published"] is True


@pytest.mark.asyncio
async def test_user_posts_visibility(client: AsyncClient, test_user_token: str) -> None:
    headers_owner = {"Authorization": f"Bearer {test_user_token}"}

    me = await client.get("/api/v1/users", headers=headers_owner)
    username = me.json()[0]["username"]

    await client.post(
        "/api/v1/posts",
        headers=headers_owner,
        json={"title": "Draft", "body": "Draft content", "is_published": False},
    )

    # Успех: Автор видит свой черновик в списке своих постов
    res_my_list = await client.get(
        f"/api/v1/users/{username}/posts",
        headers=headers_owner,
    )
    assert len(res_my_list.json()) == 1

    # Ошибка: Аноним видит пустой список постов этого юзера
    res_anon_list = await client.get(f"/api/v1/users/{username}/posts")
    assert len(res_anon_list.json()) == 0


@pytest.mark.asyncio
async def test_partial_update_does_not_reset_status(
    client: AsyncClient,
    test_user_token: str,
) -> None:
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Создание поста
    res = await client.post(
        "/api/v1/posts",
        headers=headers,
        json={
            "title": "Old Title",
            "body": "Original content...",
            "is_published": True,
        },
    )
    post_id = res.json()["id"]

    # Обновление ТОЛЬКО заголовка
    await client.patch(
        f"/api/v1/posts/{post_id}", headers=headers, json={"title": "New Title"}
    )

    # Проверка, что пост ВСЁ ЕЩЕ опубликован
    res_final = await client.get(f"/api/v1/posts/{post_id}")
    assert res_final.json()["title"] == "New Title"
    assert res_final.json()["is_published"] is True
