import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import Iterable, List

import aiohttp
from aiohttp import ClientError

from yacut.constants import (
    YANDEX_API_BASE_URL,
    YANDEX_DOWNLOAD_ENDPOINT,
    YANDEX_UPLOAD_ENDPOINT,
)
from yacut.models import URLMap


# Сообщения об ошибках
YANDEX_API_ERROR = 'Ошибка обращения к API Яндекс Диска ({status}): {detail}'
UPLOAD_LINK_ERROR = (
    'Сервис Яндекс Диска не вернул ссылку для загрузки файла.'
)
DOWNLOAD_LINK_ERROR = (
    'Сервис Яндекс Диска не вернул ссылку для скачивания файла.'
)
TOKEN_MISSING_ERROR = 'Не задан токен доступа к Яндекс Диску.'
API_REQUEST_ERROR = 'Ошибка при обращении к API Яндекс Диска.'


class YandexDiskServiceError(Exception):
    """Базовое исключение сервиса Яндекс.Диска."""


@dataclass
class FileToUpload:
    filename: str
    content: bytes


@dataclass
class UploadedFile:
    filename: str
    short: str
    original_url: str


async def _raise_for_status(response):
    if response.status < HTTPStatus.BAD_REQUEST:
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
        YANDEX_API_ERROR.format(status=response.status, detail=detail)
    )


def _sanitize_filename(filename: str) -> str:
    return filename.replace('/', '_').replace('\\', '_')


def _build_disk_path(short: str, filename: str) -> str:
    safe_name = _sanitize_filename(filename)
    return f'app:/yacut_{short}_{safe_name}'


async def _request_upload_link(
    session: aiohttp.ClientSession,
    token: str,
    path: str,
) -> str:
    params = {
        'path': path,
        'overwrite': 'true',
    }
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
        raise YandexDiskServiceError(UPLOAD_LINK_ERROR)
    return href


async def _upload_file_content(
    session: aiohttp.ClientSession,
    href: str,
    content: bytes,
) -> None:
    async with session.put(href, data=content) as response:
        await _raise_for_status(response)


async def _request_download_link(
    session: aiohttp.ClientSession,
    token: str,
    path: str,
) -> str:
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
        raise YandexDiskServiceError(DOWNLOAD_LINK_ERROR)
    return href


async def _upload_single_file(
    session: aiohttp.ClientSession,
    token: str,
    file: FileToUpload,
) -> UploadedFile:
    short = URLMap.get_unique_short()
    path = _build_disk_path(short, file.filename)
    upload_href = await _request_upload_link(session, token, path)
    await _upload_file_content(session, upload_href, file.content)
    download_href = await _request_download_link(session, token, path)
    return UploadedFile(
        filename=file.filename,
        short=short,
        original_url=download_href,
    )


async def _upload_files_async(
    files: List[FileToUpload],
    token: str,
) -> List[UploadedFile]:
    async with aiohttp.ClientSession() as session:
        results: List[UploadedFile] = []
        for file in files:
            results.append(await _upload_single_file(session, token, file))
        return results


def prepare_files_for_upload(file_storages):
    """Преобразует FileStorage объекты в FileToUpload."""
    return (
        FileToUpload(filename=storage.filename, content=storage.read())
        for storage in file_storages
    )


def upload_files_to_yandex_disk(
    files: Iterable[FileToUpload],
    *,
    token: str,
) -> List[UploadedFile]:
    file_list = list(files)
    if not file_list:
        return []
    if not token:
        raise YandexDiskServiceError(TOKEN_MISSING_ERROR)
    try:
        return asyncio.run(_upload_files_async(file_list, token))
    except YandexDiskServiceError:
        raise
    except (ClientError, asyncio.TimeoutError) as exc:
        raise YandexDiskServiceError(API_REQUEST_ERROR) from exc
