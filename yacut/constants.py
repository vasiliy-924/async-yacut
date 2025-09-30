import string

# Generator
ALPHABET = string.ascii_letters + string.digits
DEFAULT_SHORT_LENGTH = 6
MIN_SHORT_ID_LENGTH = 1
MAX_SHORT_ID_LENGTH = 16
RESERVED_SHORT_IDS = frozenset({'files'})
INVALID_SHORT_ID_MSG = 'Указано недопустимое имя для короткой ссылки'
DUPLICATE_SHORT_ID_MSG = 'Предложенный вариант короткой ссылки уже существует.'
MAX_GENERATION_ATTEMPTS = 1000
MAX_URL_LENGTH = 2048
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_ERROR = 500

# Yandex Disk API
YANDEX_API_BASE_URL = 'https://cloud-api.yandex.net'
YANDEX_UPLOAD_ENDPOINT = '/v1/disk/resources/upload'
YANDEX_DOWNLOAD_ENDPOINT = '/v1/disk/resources/download'
YANDEX_UPLOAD_ROOT = 'app:/yacut'
YANDEX_OVERWRITE_PARAM_VALUE = 'true'
YANDEX_PATH_PARAM = 'path'
YANDEX_OVERWRITE_PARAM_NAME = 'overwrite'