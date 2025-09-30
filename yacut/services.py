import asyncio
import secrets
from dataclasses import dataclass
from typing import Iterable, List

import aiohttp
from aiohttp import ClientError
from sqlalchemy import select

from yacut import db
from yacut.constants import (
    ALPHABET,
    DEFAULT_SHORT_LENGTH,
    MAX_GENERATION_ATTEMPTS,
    RESERVED_SHORT_IDS,
)
from yacut.models import URLMap


YANDEX_API_BASE_URL = 'https://cloud-api.yandex.net'
YANDEX_UPLOAD_ENDPOINT = '/v1/disk/resources/upload'
YANDEX_DOWNLOAD_ENDPOINT = '/v1/disk/resources/download'
YANDEX_UPLOAD_ROOT = 'app:/yacut'


class YandexDiskServiceError(Exception):
    """Базовое исключение сервиса Яндекс.Диска."""


@dataclass
class FileToUpload:
    filename: str
    content: bytes


@dataclass
class UploadedFile:
    filename: str
    short_id: str
    original_url: str


def get_unique_short_id(length=DEFAULT_SHORT_LENGTH):
    attempts = 0
    while attempts < MAX_GENERATION_ATTEMPTS:
        candidate = ''.join(secrets.choice(ALPHABET) for _ in range(length))
        if candidate in RESERVED_SHORT_IDS:
            attempts += 1
            continue
        if not db.session.execute(
            select(URLMap.id).filter_by(short=candidate)
        ).scalar():
            return candidate
        attempts += 1
    raise RuntimeError('Не удалось сгенерировать уникальный идентификатор')


async def _raise_for_status(response):
    if response.status < 400:
        return
    detail: str = ''
    try:
        payload = await response.json()
    except Exception:
        payload = await response.text()
    if isinstance(payload, dict):
        detail = payload.get('message') or str(payload)
    elif isinstance(payload, str):
        detail = payload
    raise YandexDiskServiceError(
        f'Ошибка обращения к API Яндекс Диска ({response.status}): {detail}'
    )


def _sanitize_filename(filename: str) -> str:
    return filename.replace('/', '_').replace('\\', '_')


def _build_disk_path(short_id: str, filename: str) -> str:
    safe_name = _sanitize_filename(filename)
    return f'{YANDEX_UPLOAD_ROOT}_{short_id}_{safe_name}'


async def _request_upload_link(session: aiohttp.ClientSession, token: str, path: str) -> str:
    params = {'path': path, 'overwrite': 'true'}
    headers = {'Authorization': f'OAuth {token}'}
    async with session.get(
        f'{YANDEX_API_BASE_URL}{YANDEX_UPLOAD_ENDPOINT}',
        params=params,
        headers=headers,
    ) as response:
        await _raise_for_status(response)
        data = await response.json()
    href = data.get('href')
    if not href:
        raise YandexDiskServiceError('Сервис Яндекс Диска не вернул ссылку для загрузки файла.')
    return href


async def _upload_file_content(session: aiohttp.ClientSession, href: str, content: bytes) -> None:
    async with session.put(href, data=content) as response:
        await _raise_for_status(response)


async def _request_download_link(session: aiohttp.ClientSession, token: str, path: str) -> str:
    params = {'path': path}
    headers = {'Authorization': f'OAuth {token}'}
    async with session.get(
        f'{YANDEX_API_BASE_URL}{YANDEX_DOWNLOAD_ENDPOINT}',
        params=params,
        headers=headers,
    ) as response:
        await _raise_for_status(response)
        data = await response.json()
    href = data.get('href')
    if not href:
        raise YandexDiskServiceError('Сервис Яндекс Диска не вернул ссылку для скачивания файла.')
    return href


async def _upload_single_file(
    session: aiohttp.ClientSession,
    token: str,
    file: FileToUpload,
) -> UploadedFile:
    short_id = get_unique_short_id()
    path = _build_disk_path(short_id, file.filename)
    upload_href = await _request_upload_link(session, token, path)
    await _upload_file_content(session, upload_href, file.content)
    download_href = await _request_download_link(session, token, path)
    return UploadedFile(filename=file.filename, short_id=short_id, original_url=download_href)


async def _upload_files_async(files: List[FileToUpload], token: str) -> List[UploadedFile]:
    async with aiohttp.ClientSession() as session:
        results: List[UploadedFile] = []
        for file in files:
            results.append(await _upload_single_file(session, token, file))
        return results


def upload_files_to_yandex_disk(
    files: Iterable[FileToUpload],
    *,
    token: str,
) -> List[UploadedFile]:
    file_list = list(files)
    if not file_list:
        return []
    if not token:
        raise YandexDiskServiceError('Не задан токен доступа к Яндекс Диску.')
    try:
        return asyncio.run(_upload_files_async(file_list, token))
    except YandexDiskServiceError:
        raise
    except (ClientError, asyncio.TimeoutError) as exc:
        raise YandexDiskServiceError('Ошибка при обращении к API Яндекс Диска.') from exc