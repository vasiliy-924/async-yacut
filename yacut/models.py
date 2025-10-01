import secrets
from datetime import datetime

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
    RESERVED_SHORTS,
    SHORT_CHARS,
)

INVALID_SHORT = 'Указано недопустимое имя для короткой ссылки'
DUPLICATE_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
UNIQUE_SHORT_GENERATION_ERROR = (
    'Не удалось сгенерировать уникальный идентификатор'
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

    @classmethod
    def create(cls, original: str, short: str, *, commit: bool = True):
        """Создает новую запись URL-маппинга."""
        url_map = cls(original=original, short=short)
        db.session.add(url_map)
        if commit:
            db.session.commit()
        return url_map

    @classmethod
    def find_by_short(cls, short: str):
        """Находит запись по короткому идентификатору."""
        return db.session.execute(
            select(cls).filter_by(short=short)
        ).scalar_one_or_none()

    @classmethod
    def short_exists(cls, short: str) -> bool:
        """Проверяет существование короткого идентификатора."""
        return db.session.execute(
            select(cls.id).filter_by(short=short)
        ).scalar() is not None

    @classmethod
    def get_unique_short(cls) -> str:
        """Генерирует уникальный короткий идентификатор."""
        for _ in range(MAX_GENERATION_ATTEMPTS):
            candidate = ''.join(
                secrets.choice(SHORT_CHARS)
                for _ in range(DEFAULT_SHORT_LENGTH)
            )
            if candidate in RESERVED_SHORTS:
                continue
            if not cls.short_exists(candidate):
                return candidate
        raise RuntimeError(UNIQUE_SHORT_GENERATION_ERROR)

    @classmethod
    def validate_short(cls, value, *, require=False, check_unique=False):
        """Валидация короткого идентификатора."""
        if value is None:
            if require:
                raise ValidationError(INVALID_SHORT)
            return None

        trimmed = value.strip()
        if not trimmed:
            if require:
                raise ValidationError(INVALID_SHORT)
            return None

        if len(trimmed) > MAX_SHORT_LENGTH:
            raise ValidationError(INVALID_SHORT)

        if trimmed in RESERVED_SHORTS:
            raise ValidationError(DUPLICATE_SHORT)

        if not ALLOWED_SHORT_PATTERN.fullmatch(trimmed):
            raise ValidationError(INVALID_SHORT)

        if check_unique and cls.short_exists(trimmed):
            raise ValidationError(DUPLICATE_SHORT)

        return trimmed

    def get_short_url(self) -> str:
        """Возвращает полный короткий URL."""
        return url_for('redirect_view', short=self.short, _external=True)

    def to_dict(self):
        """Возвращает словарь с данными маппинга."""
        return dict(
            id=self.id,
            original=self.original,
            short=self.short,
            timestamp=self.timestamp
        )
