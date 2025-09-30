# тут будут утилиты (или переименовать в services)

import secrets

from sqlalchemy import select

from yacut import db
from yacut.constants import (
    ALPHABET,
    DEFAULT_SHORT_LENGTH,
    MAX_SHORT_ID_LENGTH,
)
from yacut.models import URLMap


def get_unique_short_id(length=DEFAULT_SHORT_LENGTH):
    current_length = length
    while current_length <= MAX_SHORT_ID_LENGTH:
        candidate = ''.join(secrets.choice(ALPHABET) for _ in range(current_length))
        if not db.session.execute(
            select(URLMap.id).filter_by(short=candidate)
        ).scalar():
            return candidate
        current_length += 1
    raise RuntimeError('Не удалось сгенерировать уникальный идентификатор')