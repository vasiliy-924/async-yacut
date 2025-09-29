import re

from wtforms import ValidationError

from yacut.constants import (
    DUPLICATE_SHORT_ID_MSG,
    INVALID_SHORT_ID_MSG,
    MAX_SHORT_ID_LENGTH,
    MIN_SHORT_ID_LENGTH,
    RESERVED_SHORT_IDS,
)
from yacut.models import URLMap

_ALLOWED_PATTERN = re.compile(r'^[A-Za-z0-9]+$')


def validate_unique_short_id(value, *, require, check_unique):
    """
    Проверка пользовательского короткого идентификатора во всех точках входа.
    """

    if value is None:
        if require:
            raise ValidationError(INVALID_SHORT_ID_MSG)
        return None

    trimmed = value.strip()
    if not trimmed:
        if require:
            raise ValidationError(INVALID_SHORT_ID_MSG)
        return None

    if len(trimmed) < MIN_SHORT_ID_LENGTH or len(trimmed) > MAX_SHORT_ID_LENGTH:
        raise ValidationError(INVALID_SHORT_ID_MSG)

    if trimmed in RESERVED_SHORT_IDS:
        raise ValidationError(DUPLICATE_SHORT_ID_MSG)

    if not _ALLOWED_PATTERN.fullmatch(trimmed):
        raise ValidationError(INVALID_SHORT_ID_MSG)

    if check_unique and URLMap.query.filter_by(short=trimmed).first() is not None:
        raise ValidationError(DUPLICATE_SHORT_ID_MSG)

    return trimmed
