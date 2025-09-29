# тут будут константы проекта

import string

# Generator
ALPHABET = string.ascii_letters + string.digits
DEFAULT_SHORT_LENGTH = 6
MIN_SHORT_ID_LENGTH = 1
MAX_SHORT_ID_LENGTH = 16
RESERVED_SHORT_IDS = frozenset({'files'})
INVALID_SHORT_ID_MSG = 'Указано недопустимое имя для короткой ссылки'
DUPLICATE_SHORT_ID_MSG = 'Предложенный вариант короткой ссылки уже существует.'