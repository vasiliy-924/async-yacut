# тут будут утилиты (или переименовать в services)

import secrets

from yacut.constants import ALPHABET, DEFAULT_SHORT_LENGTH


def get_unique_short_id(length=DEFAULT_SHORT_LENGTH):
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))