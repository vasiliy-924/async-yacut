import re
import string

# Generator
SHORT_CHARS = string.ascii_letters + string.digits
ALLOWED_SHORT_PATTERN = re.compile(
    rf'^[{re.escape(SHORT_CHARS)}]+$'
)
DEFAULT_SHORT_LENGTH = 6
MAX_SHORT_LENGTH = 16
RESERVED_SHORTS = frozenset({'files'})
MAX_GENERATION_ATTEMPTS = 1000
MAX_URL_LENGTH = 2048

# File upload
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp',
    'zip', 'rar', '7z', 'tar', 'gz',
    'mp3', 'mp4', 'avi', 'mkv', 'mov',
    'json', 'xml', 'csv', 'html', 'css', 'js', 'py',
}

# Yandex Disk API
YANDEX_API_BASE_URL = 'https://cloud-api.yandex.net'
YANDEX_UPLOAD_ENDPOINT = '/v1/disk/resources/upload'
YANDEX_DOWNLOAD_ENDPOINT = '/v1/disk/resources/download'
YANDEX_UPLOAD_ROOT = 'app:/yacut'
YANDEX_OVERWRITE_PARAM_VALUE = 'true'
YANDEX_PATH_PARAM = 'path'
YANDEX_OVERWRITE_PARAM_NAME = 'overwrite'
