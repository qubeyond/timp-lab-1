import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Post, User
from src.schemas import PostCreate, PostUpdate


class UserCRUD:
    # GET

    @staticmethod
    async def get_all_users(
        db: AsyncSession,
        include_deleted: bool = False,
    ) -> list[User]:
        """Получение списка пользователей с фильтром удаления."""

        query = select(User)
        if not include_deleted:
            query = query.where(User.is_deleted == False)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def find_user_by_uuid(
        db: AsyncSession,
        user_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> User | None:
        """Получение пользователя по UUID с фильтром удаления."""

        user = await db.get(User, user_id)
        if user and not include_deleted and user.is_deleted:
            return None

        return user

    @staticmethod
    async def find_user_by_username(
        db: AsyncSession,
        username: str,
        include_deleted: bool = False,
    ) -> User | None:
        """Получение пользователя по имени с фильтром удаления."""

        query = select(User).where(User.username == username)
        if not include_deleted:
            query = query.where(User.is_deleted == False)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    # CREATE

    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        hashed_password: str,
    ) -> User:
        """Создание нового пользователя."""

        new_user = User(username=username, hashed_password=hashed_password)
        db.add(new_user)

        await db.flush()
        return new_user

    # UPDATE

    @staticmethod
    async def update_user_obj(
        db: AsyncSession,
        user: User,
        new_username: str,
    ) -> User:
        """Обновление пользователя. Принимает объект."""

        user.username = new_username

        await db.flush()
        return user

    @staticmethod
    async def update_last_login(
        db: AsyncSession,
        user: User,
    ) -> User:
        """Обновление времени последнего входа пользователя."""

        user.last_login = datetime.now(UTC)

        await db.flush()
        return user

    # DELETE

    @staticmethod
    async def soft_delete_user_obj(
        db: AsyncSession,
        user: User,
    ) -> None:
        """Удаление пользователя (мягкое удаление). Принимает объект."""

        user.is_deleted = True
        await db.flush()


class PostCRUD:
    # GET

    @staticmethod
    async def get_all_posts(
        db: AsyncSession,
        include_unpublished: bool = False,
    ) -> list[Post]:
        """Получение списка постов с фильтром публикации."""

        query = select(Post)
        if not include_unpublished:
            query = query.where(Post.is_published == True)

        result = await db.execute(query.order_by(Post.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def find_post_by_uuid(
        db: AsyncSession,
        post_id: uuid.UUID,
        include_unpublished: bool = False,
    ) -> Post | None:
        """Получение поста по UUID с фильтром публикации."""

        post = await db.get(Post, post_id)
        if post and not include_unpublished and not post.is_published:
            return None

        return post

    @staticmethod
    async def get_posts_by_owner_uuid(
        db: AsyncSession,
        owner_id: uuid.UUID,
        include_unpublished: bool = False,
    ) -> list[Post]:
        """Получение постов владельца с фильтром публикации."""

        query = select(Post).where(Post.owner_id == owner_id)
        if not include_unpublished:
            query = query.where(Post.is_published == True)

        result = await db.execute(query.order_by(Post.created_at.desc()))
        return list(result.scalars().all())

    # CREATE

    @staticmethod
    async def create_post(
        db: AsyncSession,
        post_in: PostCreate,
        owner_id: uuid.UUID,
    ) -> Post:
        """Создание нового поста."""

        new_post = Post(**post_in.model_dump(), owner_id=owner_id)

        db.add(new_post)
        await db.flush()
        return new_post

    # UPDATE

    @staticmethod
    async def update_post_obj(
        db: AsyncSession,
        post: Post,
        post_in: PostUpdate,
    ) -> Post:
        """Обновление поста. Принимает объект."""

        update_data = post_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(post, key, value)

        await db.flush()
        return post

    # DELETE

    @staticmethod
    async def soft_delete_post_obj(
        db: AsyncSession,
        post: Post,
    ) -> None:
        """Удаление поста (мягкое удаление). Принимает объект."""

        post.is_published = False
        await db.flush()
