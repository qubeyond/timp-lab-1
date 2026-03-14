import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.cruds import PostCRUD, UserCRUD
from src.database import get_db
from src.schemas import (
    PostCreate,
    PostResponse,
    PostUpdate,
    Token,
    UserCreate,
    UserResponse,
)
from src.security import SecurityService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


# Dependency


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user_id_str = SecurityService.decode_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_uuid = uuid.UUID(user_id_str)
    user_obj = await UserCRUD.get_user_by_id(db, user_uuid)

    if not user_obj or user_obj.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user_obj)


# Auth Routers


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await UserCRUD.register_user(db, user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    tags=["Auth"],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await UserCRUD.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = SecurityService.create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
)
async def logout(
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    """
    В текущей реализации JWT logout происходит на стороне клиента
    путем удаления токена. Этот эндпоинт зарезервирован для
    будущей реализации черного списка токенов.
    """
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
    users = await UserCRUD.get_all_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.patch(
    "/users/me",
    response_model=UserResponse,
    tags=["Users"],
)
async def change_my_username(
    new_username: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    updated_user = await UserCRUD.update_username(db, current_user.id, new_username)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users"],
)
async def delete_my_account(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await UserCRUD.soft_delete_user(db, current_user.id)
    return None


# Posts Routers


@router.get(
    "/posts",
    response_model=list[PostResponse],
    tags=["Posts"],
)
async def read_posts(
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    posts = await PostCRUD.get_all_posts(db)
    return [PostResponse.model_validate(p) for p in posts]


@router.get(
    "/posts/{post_id}",
    response_model=PostResponse,
    tags=["Posts"],
)
async def read_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    post = await PostCRUD.get_post_by_uuid(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return PostResponse.model_validate(post)


@router.get(
    "/users/{username}/posts",
    response_model=list[PostResponse],
    tags=["Posts"],
)
async def read_user_posts(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    user_posts = await PostCRUD.get_posts_by_username(db, username)
    return [PostResponse.model_validate(p) for p in user_posts]


@router.post(
    "/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Posts"],
)
async def create_post(
    post_in: PostCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    post = await PostCRUD.create_post(db, post_in, current_user.id)
    return PostResponse.model_validate(post)


@router.patch(
    "/posts/{post_id}",
    response_model=PostResponse,
    tags=["Posts"],
)
async def update_post(
    post_id: uuid.UUID,
    post_in: PostUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    updated_post = await PostCRUD.update_post(db, post_id, post_in, current_user.id)
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized or post not found",
        )
    return PostResponse.model_validate(updated_post)


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Posts"],
)
async def delete_post(
    post_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    success = await PostCRUD.soft_delete_post(db, post_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized or post not found",
        )
    return None
