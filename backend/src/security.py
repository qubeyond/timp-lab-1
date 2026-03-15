from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from src.settings import settings


class SecurityService:
    """Технический сервис для работы с паролями и токенами."""

    @staticmethod
    def verify_password(
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """Проверка соответствия сырого пароля его хешу."""

        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def hash_password(
        password: str,
    ) -> str:
        """Хеширование пароля."""

        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def decode_access_token(
        token: str,
    ) -> str | None:
        """Декодирование JWT токена."""

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload.get("sub")
        except jwt.PyJWTError:
            return None

    @staticmethod
    def create_access_token(
        data: dict,
    ) -> str:
        """Создание нового JWT токена."""

        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
