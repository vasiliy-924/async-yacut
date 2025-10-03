import random
from datetime import datetime
from urllib.parse import urlparse

from flask import url_for
from sqlalchemy import select
from wtforms import ValidationError

from yacut import db
from yacut.constants import (
    ALLOWED_SHORT_PATTERN,
    DEFAULT_SHORT_LENGTH,
    MAX_GENERATION_ATTEMPTS,
    MAX_SHORT_LENGTH,
    MAX_URL_LENGTH,
    REDIRECT_VIEW_NAME,
    RESERVED_SHORTS,
    SHORT_CHARS,
)

INVALID_SHORT = 'Указано недопустимое имя для короткой ссылки'
DUPLICATE_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
UNIQUE_SHORT_GENERATION_ERROR = (
    f'Не удалось сгенерировать уникальный идентификатор '
    f'за {MAX_GENERATION_ATTEMPTS} попыток'
)


class URLMap(db.Model):
    """Микро-ORM для работы с короткими ссылками."""

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    short = db.Column(
        db.String(MAX_SHORT_LENGTH),
        nullable=False,
        unique=True
    )
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def create(
        original: str,
        short: str = None,
        *,
        commit: bool = True,
        validate: bool = True
    ):
        """Создает новую запись URL-маппинга."""
        if validate:
            parsed = urlparse(original)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            if short:
                URLMap.validate_short(short, require=True, check_unique=True)

        if not short:
            short = URLMap.get_unique_short()

        url_map = URLMap(original=original, short=short)
        db.session.add(url_map)
        if commit:
            db.session.commit()

        return url_map

    @staticmethod
    def find(short: str):
        """Находит запись по короткому идентификатору."""
        return db.session.execute(
            select(URLMap).filter_by(short=short)
        ).scalar_one_or_none()

    @staticmethod
    def get_unique_short() -> str:
        """Генерирует уникальный короткий идентификатор."""
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            candidate = ''.join(
                random.choices(SHORT_CHARS, k=DEFAULT_SHORT_LENGTH)
            )
            if candidate not in RESERVED_SHORTS and not URLMap.find(candidate):
                return candidate
        raise RuntimeError(UNIQUE_SHORT_GENERATION_ERROR)

    @staticmethod
    def validate_short(value, *, require=False, check_unique=False):
        """Валидация короткого идентификатора."""
        if value is None or not value or not value.strip():
            if require:
                raise ValidationError(INVALID_SHORT)
            return value

        trimmed = value.strip()

        if len(trimmed) > MAX_SHORT_LENGTH:
            raise ValidationError(INVALID_SHORT)

        if trimmed in RESERVED_SHORTS:
            raise ValidationError(DUPLICATE_SHORT)

        if not ALLOWED_SHORT_PATTERN.fullmatch(trimmed):
            raise ValidationError(INVALID_SHORT)

        if check_unique and URLMap.find(trimmed):
            raise ValidationError(DUPLICATE_SHORT)

        return trimmed

    def get_short_url(self) -> str:
        """Возвращает полный короткий URL."""
        return url_for(REDIRECT_VIEW_NAME, short=self.short, _external=True)
