import uuid

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import User
from src.schemas import (
    AuthResponse,
    PostCreate,
    PostResponse,
    PostUpdate,
    Token,
    UserCreate,
    UserResponse,
)
from src.security import SecurityService
from src.services import AuthService, PostService, UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


# Dependency


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Получение текущего пользователя по токену."""

    return await AuthService.get_user_from_token(db, token)


async def get_optional_user(
    token: str | None = Depends(
        OAuth2PasswordBearer(tokenUrl="api/v1/login", auto_error=False),
    ),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Зависимость для необязательной авторизации."""

    if not token:
        return None

    try:
        return await AuthService.get_user_from_token(db, token)

    except Exception:
        return None


# Auth Routers


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Регистрация аккаунта."""

    return await AuthService.register_and_login(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    tags=["Auth"],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Вход в аккаунт по логину и паролю."""

    user = await AuthService.authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    token = SecurityService.create_access_token(data={"sub": str(user.id)})

    return Token(access_token=token, token_type="Bearer")


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> None:
    """Выход из аккаунта."""

    await AuthService.logout_user(current_user)
    return None


# Users Routers


@router.get(
    "/users",
    response_model=list[UserResponse],
    tags=["Users"],
)
async def read_users(
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """Посмотреть всех пользователей."""

    return await UserService.get_active_users(db)


@router.get(
    "/users/profile/{username}",
    response_model=UserResponse,
    tags=["Users"],
)
async def get_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Посмотреть профиль пользователя."""

    return await UserService.get_user_profile(db, username)


@router.patch(
    "/users/me",
    response_model=UserResponse,
    tags=["Users"],
)
async def change_my_username(
    new_username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Обновить свой профиль."""

    return await UserService.update_my_username(db, current_user, new_username)


# Posts Routers


@router.get(
    "/posts",
    response_model=list[PostResponse],
    tags=["Posts"],
)
async def read_posts(
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """Посмотреть все посты."""

    return await PostService.get_public_posts(db)


@router.get(
    "/posts/{post_id}",
    response_model=PostResponse,
    tags=["Posts"],
)
async def read_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> PostResponse:
    """Посмотреть пост. Автор видит свои черновики."""

    viewer_id = getattr(current_user, "id", None)
    return await PostService.get_post_or_404(db, post_id, viewer_id=viewer_id)


@router.get(
    "/users/{username}/posts",
    response_model=list[PostResponse],
    tags=["Posts"],
)
async def read_user_posts(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> list[PostResponse]:
    """Посмотреть все посты пользователя. Автор видит свои черновики."""

    target_user = await UserService.get_user_profile(db, username)
    viewer_id = getattr(current_user, "id", None)

    return await PostService.get_user_posts(
        db,
        target_user.id,
        current_user_id=viewer_id,
    )


@router.post(
    "/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Posts"],
)
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """Создать пост."""

    return await PostService.create_new_post(db, post_in, current_user.id)


@router.patch(
    "/posts/{post_id}",
    response_model=PostResponse,
    tags=["Posts"],
)
async def update_post(
    post_id: uuid.UUID,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    """Обновить пост."""

    return await PostService.update_post(db, post_id, post_in, current_user.id)


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Posts"],
)
async def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить пост."""

    await PostService.delete_post(db, post_id, current_user.id)
    return None
