import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.cruds import PostCRUD, UserCRUD
from src.models import Post, User
from src.schemas import PostCreate, PostUpdate, UserCreate
from src.security import SecurityService


class AuthService:
    """Бизнес-сервис для управления доступом и безопасностью."""

    @staticmethod
    async def register_and_login(
        db: AsyncSession,
        user_in: UserCreate,
    ) -> dict:
        """Регистрация пользователя и вход."""

        hashed_password = SecurityService.hash_password(user_in.password)

        try:
            user = await UserCRUD.create_user(
                db,
                user_in.username,
                hashed_password,
            )
            await db.commit()
            await db.refresh(user)

        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            ) from None

        token = SecurityService.create_access_token(data={"sub": str(user.id)})

        return {
            "user": user,
            "access_token": token,
            "token_type": "Bearer",
        }

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User:
        user = await UserCRUD.find_user_by_username(db, username)

        if not user or not SecurityService.verify_password(
            password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        updated_user = await UserCRUD.update_last_login(db, user)

        await db.commit()
        await db.refresh(updated_user)
        return updated_user

    @staticmethod
    async def get_user_from_token(
        db: AsyncSession,
        token: str,
    ) -> User:
        """Получение пользователя по токену."""

        user_id_str = SecurityService.decode_access_token(token)

        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_uuid = uuid.UUID(user_id_str)
        return await UserService.get_user_or_404(db, user_uuid)

    @staticmethod
    async def logout_user(
        current_user: User,
    ) -> None:
        """Выход из аккаунта пользователя."""

        # На данный момент JWT удаляется на клиенте.
        # Здесь должна быть логика добавления токена в blacklist.
        return None


class UserService:
    """Бизнес-сервис для управления пользователями."""

    @staticmethod
    async def get_active_users(
        db: AsyncSession,
    ) -> list[User]:
        """Получение всех активных пользователей."""

        return await UserCRUD.get_all_users(db)

    @staticmethod
    async def get_user_or_404(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> User:
        """Получение пользователя или 404."""

        user = await UserCRUD.find_user_by_uuid(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    @staticmethod
    async def get_user_profile(
        db: AsyncSession,
        username: str,
    ) -> User:
        """Поиск публичного профиля по username."""

        user = await UserCRUD.find_user_by_username(db, username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )

        return user

    @staticmethod
    async def update_my_username(
        db: AsyncSession,
        user_obj: User,
        new_username: str,
    ) -> User:
        """Смена имени текущего пользователя."""

        if user_obj.username == new_username:
            return user_obj

        try:
            updated_user = await UserCRUD.update_user_obj(db, user_obj, new_username)
            await db.commit()
            await db.refresh(updated_user)
            return updated_user

        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            ) from None


class PostService:
    """Бизнес-сервис для управления постами."""

    @staticmethod
    async def get_public_posts(
        db: AsyncSession,
    ) -> list[Post]:
        """Получение всех опубликованных постов."""

        return await PostCRUD.get_all_posts(db)

    @staticmethod
    async def get_post_or_404(
        db: AsyncSession,
        post_id: uuid.UUID,
    ) -> Post:
        """Получение поста или ошибка 404."""

        post = await PostCRUD.find_post_by_uuid(
            db,
            post_id,
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        return post

    @staticmethod
    async def get_user_posts(
        db: AsyncSession,
        owner_id: uuid.UUID,
    ) -> list[Post]:
        """Получение всех постов пользователя."""

        return await PostCRUD.get_posts_by_owner_uuid(db, owner_id)

    @staticmethod
    async def create_new_post(
        db: AsyncSession,
        post_in: PostCreate,
        owner_id: uuid.UUID,
    ) -> Post:
        """Создание нового поста."""

        try:
            post = await PostCRUD.create_post(db, post_in, owner_id)
            await db.commit()
            await db.refresh(post)
            return post

        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error during post creation",
            ) from None

    @staticmethod
    async def update_post(
        db: AsyncSession,
        post_id: uuid.UUID,
        post_in: PostUpdate,
        user_id: uuid.UUID,
    ) -> Post:
        """Редактирование поста с проверкой прав."""

        post = await PostService.get_post_or_404(db, post_id)

        if post.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this post",
            )

        updated_post = await PostCRUD.update_post_obj(db, post, post_in)

        await db.commit()
        await db.refresh(updated_post)
        return updated_post

    @staticmethod
    async def delete_post(
        db: AsyncSession,
        post_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Мягкое удаление поста."""

        post = await PostService.get_post_or_404(db, post_id)

        if post.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this post",
            )

        await PostCRUD.soft_delete_post_obj(db, post)
        await db.commit()
