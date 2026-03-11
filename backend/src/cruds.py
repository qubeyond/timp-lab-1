import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import User, Post
from src.schemas import (
    UserResponse, UserCreate, 
    PostResponse, PostCreate, PostUpdate
)
from src.security import verify_password, hash_password


# Auth Cruds

async def register_user(
        db: AsyncSession, 
        user_in: UserCreate
) -> UserResponse | None:
    existing_user = await get_user_by_username(
        db, 
        user_in.username
    )
    if existing_user:
        return None
    
    return await create_user(db, user_in)


async def authenticate_user(
        db: AsyncSession, 
        username: str, 
        password: str
) -> UserResponse | None:
    query = select(User).where(
        User.username == username, 
        User.is_deleted == False
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(
        password, 
        user.hashed_password
    ):
        return None
        
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


# User Cruds

async def get_all_users(
        db: AsyncSession
) -> list[UserResponse]:
    query = select(User).where(
        User.is_deleted == False
    )
    result = await db.execute(query)
    return [
        UserResponse.model_validate(u) 
        for u in result.scalars().all()
    ]


async def get_user_by_id(
        db: AsyncSession, 
        user_id: uuid.UUID
    ) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_username(
        db: AsyncSession, 
        username: str
) -> UserResponse | None:
    query = select(User).where(
        User.username == username,
        User.is_deleted == False
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return UserResponse.model_validate(user) if user else None


async def create_user(
        db: AsyncSession, 
        user_in: UserCreate
) -> UserResponse:
    new_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password) 
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse.model_validate(new_user)


async def update_username(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    new_username: str
) -> UserResponse | None:
    exists = await get_user_by_username(
        db, 
        new_username
    )
    if exists:
        return None 

    query = select(User).where(
        User.id == user_id
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        user.username = new_username
        await db.commit()
        await db.refresh(user)
        return UserResponse.model_validate(user)
    return None


async def soft_delete_user(
        db: AsyncSession, 
        user_id: uuid.UUID
) -> UserResponse | None:
    query = select(User).where(
        User.id == user_id
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        user.is_deleted = True
        await db.commit()
        await db.refresh(user)
        return UserResponse.model_validate(user)
    return None


# Post Cruds

async def get_all_posts(
        db: AsyncSession
) -> list[PostResponse]:
    query = select(Post).where(
        Post.is_published == True
    )
    result = await db.execute(
        query.order_by(Post.created_at.desc())
    )
    return [
        PostResponse.model_validate(p) 
        for p in result.scalars().all()
    ]


async def get_post_by_uuid(
        db: AsyncSession, 
        post_id: uuid.UUID
) -> PostResponse | None:
    query = select(Post).where(
        Post.id == post_id
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    return PostResponse.model_validate(post) if post else None


async def get_posts_by_username(
        db: AsyncSession, 
        username: str
) -> list[PostResponse]:
    user_query = select(User).where(
        User.username == username
    )
    user_res = await db.execute(user_query)
    user = user_res.scalar_one_or_none()
    
    if not user:
        return []

    posts_query = select(Post).where(
        Post.owner_id == user.id
    )
    result = await db.execute(
        posts_query.order_by(Post.created_at.desc())
    )
    return [
        PostResponse.model_validate(p) 
        for p in result.scalars().all()
    ]


async def create_post(
    db: AsyncSession, 
    post_in: PostCreate, 
    owner_id: uuid.UUID
) -> PostResponse:
    new_post = Post(
        **post_in.model_dump(), 
        owner_id=owner_id
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return PostResponse.model_validate(new_post)


async def update_post(
    db: AsyncSession, 
    post_id: uuid.UUID, 
    post_in: PostUpdate, 
    user_id: uuid.UUID
) -> PostResponse | None:
    query = select(Post).where(
        Post.id == post_id, 
        Post.owner_id == user_id
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        return None

    for key, value in post_in.model_dump(exclude_unset=True).items():
        setattr(post, key, value)
    
    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


async def soft_delete_post(
    db: AsyncSession, 
    post_id: uuid.UUID, 
    user_id: uuid.UUID
) -> bool:
    query = select(Post).where(
        Post.id == post_id, 
        Post.owner_id == user_id
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if post:
        post.is_published = False
        await db.commit()
        return True
    return False