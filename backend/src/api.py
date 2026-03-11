import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas import (
    UserResponse, UserCreate, Token,
    PostResponse, PostCreate, PostUpdate
)
from src import cruds
from src import security

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


# Dependency

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    user_id_str = security.decode_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )
    
    user_uuid = uuid.UUID(user_id_str)
    user_obj = await cruds.get_user_by_id(db, user_uuid)
    
    if not user_obj or user_obj.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    return UserResponse.model_validate(user_obj)


# Auth & Users Routers

@router.post(
    "/register", 
    response_model=UserResponse
)
async def register(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    user = await cruds.register_user(
        db, 
        user_in
    )
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="Username already taken"
        )
    return user


@router.post(
    "/login", 
    response_model=Token
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await cruds.authenticate_user(
        db, 
        form_data.username, 
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Incorrect username or password"
        )
    
    token = security.create_access_token(
        data={"sub": str(user.id)}
    )
    return Token(access_token=token)


@router.get(
    "/users", 
    response_model=list[UserResponse]
)
async def read_users(
    db: AsyncSession = Depends(get_db)
):
    return await cruds.get_all_users(db)


@router.patch(
    "/users/me", 
    response_model=UserResponse
)
async def change_my_username(
    new_username: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await cruds.update_username(
        db, 
        current_user.id, 
        new_username
    )
    if not updated_user:
        raise HTTPException(
            status_code=400, 
            detail="Username already taken or user not found"
        )
    return updated_user


@router.delete(
    "/users/me", 
    response_model=UserResponse
)
async def delete_my_account(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await cruds.soft_delete_user(
        db, 
        current_user.id
    )


# Posts Routers

@router.get(
    "/posts", 
    response_model=list[PostResponse]
)
async def read_posts(
    db: AsyncSession = Depends(get_db)
):
    return await cruds.get_all_posts(db)


@router.get(
    "/posts/{post_id}", 
    response_model=PostResponse
)
async def read_post(
    post_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db)
):
    post = await cruds.get_post_by_uuid(
        db, 
        post_id
    )
    if not post:
        raise HTTPException(
            status_code=404, 
            detail="Post not found"
        )
    return post


@router.get(
    "/users/{username}/posts", 
    response_model=list[PostResponse]
)
async def read_user_posts(
    username: str, 
    db: AsyncSession = Depends(get_db)
):
    return await cruds.get_posts_by_username(
        db, 
        username
    )


@router.post(
    "/posts", 
    response_model=PostResponse
)
async def create_post(
    post_in: PostCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await cruds.create_post(
        db, 
        post_in, 
        current_user.id
    )


@router.patch(
    "/posts/{post_id}", 
    response_model=PostResponse
)
async def update_post(
    post_id: uuid.UUID,
    post_in: PostUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_post = await cruds.update_post(
        db, 
        post_id, 
        post_in, 
        current_user.id
    )
    if not updated_post:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized or post not found"
        )
    return updated_post


@router.delete(
    "/posts/{post_id}"
)
async def delete_post(
    post_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await cruds.soft_delete_post(
        db, 
        post_id, 
        current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized or post not found"
        )
    return {"detail": "Post deactivated"}