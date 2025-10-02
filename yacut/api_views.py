from http import HTTPStatus

from flask import Blueprint, jsonify, request
from wtforms import ValidationError

from yacut.error_handlers import APIError
from yacut.models import INVALID_SHORT, URLMap

# Сообщения об ошибках API
MSG_NO_REQUEST_BODY = 'Отсутствует тело запроса'
MSG_URL_REQUIRED = '"url" является обязательным полем!'
MSG_ID_NOT_FOUND = 'Указанный id не найден'

# Ключи JSON-ответов
JSON_KEY_URL = 'url'
JSON_KEY_SHORT_LINK = 'short_link'

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.post('/id/')
def create_short_link():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError(MSG_NO_REQUEST_BODY)

    if JSON_KEY_URL not in data:
        raise APIError(MSG_URL_REQUIRED)
    url = data[JSON_KEY_URL]
    if not url:
        raise APIError(MSG_URL_REQUIRED)

    # Поддержка обоих форматов для обратной совместимости
    try:
        short = URLMap.validate_short(
            data.get('short') or data.get('custom_id'),
            require=False,
            check_unique=True,
        )
    except ValidationError as error:
        message = error.args[0] if error.args else INVALID_SHORT
        raise APIError(message) from error

    url_map = URLMap.create(url, short)

    short_link = url_map.short_url
    return jsonify({
        JSON_KEY_URL: url,
        JSON_KEY_SHORT_LINK: short_link
    }), HTTPStatus.CREATED


@api_bp.get('/id/<string:short>/')
def get_original_link(short):
    url_map = URLMap.find(short)
    if url_map is None:
        raise APIError(MSG_ID_NOT_FOUND, HTTPStatus.NOT_FOUND)
    return jsonify({JSON_KEY_URL: url_map.original}), HTTPStatus.OK
