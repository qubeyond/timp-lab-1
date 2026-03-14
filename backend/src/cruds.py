import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Post, User
from src.schemas import PostCreate, PostUpdate, UserCreate
from src.security import SecurityService


class UserCRUD:
    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_in: UserCreate,
    ) -> User | None:
        try:
            return await UserCRUD.create_user(db, user_in)
        except IntegrityError:
            await db.rollback()
            return None

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User | None:
        query = select(User).where(
            User.username == username,
            User.is_deleted == False,
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not SecurityService.verify_password(
            password, user.hashed_password
        ):
            return None

        user.last_login = datetime.now(UTC)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_all_users(
        db: AsyncSession,
    ) -> list[User]:
        query = select(User).where(
            User.is_deleted == False,
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> User | None:
        return await db.get(User, user_id)

    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_in: UserCreate,
    ) -> User:
        new_user = User(
            username=user_in.username,
            hashed_password=SecurityService.hash_password(user_in.password),
        )
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except IntegrityError:
            await db.rollback()
            raise

    @staticmethod
    async def update_username(
        db: AsyncSession,
        user_id: uuid.UUID,
        new_username: str,
    ) -> User | None:
        user = await db.get(User, user_id)
        if user:
            user.username = new_username
            try:
                await db.commit()
                await db.refresh(user)
                return user
            except IntegrityError:
                await db.rollback()
                return None
        return None

    @staticmethod
    async def soft_delete_user(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> User | None:
        user = await db.get(User, user_id)
        if user:
            user.is_deleted = True
            await db.commit()
            await db.refresh(user)
            return user
        return None


class PostCRUD:
    @staticmethod
    async def get_all_posts(
        db: AsyncSession,
    ) -> list[Post]:
        query = select(Post).where(
            Post.is_published == True,
        )
        result = await db.execute(
            query.order_by(Post.created_at.desc()),
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_post_by_uuid(
        db: AsyncSession,
        post_id: uuid.UUID,
    ) -> Post | None:
        return await db.get(Post, post_id)

    @staticmethod
    async def get_posts_by_username(
        db: AsyncSession,
        username: str,
    ) -> list[Post]:
        user_query = select(User).where(
            User.username == username,
        )
        user_res = await db.execute(user_query)
        user = user_res.scalar_one_or_none()

        if not user:
            return []

        posts_query = select(Post).where(
            Post.owner_id == user.id,
        )
        result = await db.execute(
            posts_query.order_by(Post.created_at.desc()),
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_post(
        db: AsyncSession,
        post_in: PostCreate,
        owner_id: uuid.UUID,
    ) -> Post:
        new_post = Post(
            **post_in.model_dump(),
            owner_id=owner_id,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        return new_post

    @staticmethod
    async def update_post(
        db: AsyncSession,
        post_id: uuid.UUID,
        post_in: PostUpdate,
        user_id: uuid.UUID,
    ) -> Post | None:
        query = select(Post).where(
            Post.id == post_id,
            Post.owner_id == user_id,
        )
        result = await db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            return None

        for key, value in post_in.model_dump(exclude_unset=True).items():
            setattr(post, key, value)

        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def soft_delete_post(
        db: AsyncSession,
        post_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        query = select(Post).where(
            Post.id == post_id,
            Post.owner_id == user_id,
        )
        result = await db.execute(query)
        post = result.scalar_one_or_none()

        if post:
            post.is_published = False
            await db.commit()
            return True
        return False
