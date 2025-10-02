from http import HTTPStatus

from flask import Blueprint, jsonify, request
from wtforms import ValidationError

from yacut.error_handlers import APIError
from yacut.models import INVALID_SHORT, URLMap

# Сообщения об ошибках API
NO_REQUEST_BODY = 'Отсутствует тело запроса'
URL_REQUIRED = '"url" является обязательным полем!'
ID_NOT_FOUND = 'Указанный id не найден'

# Ключи JSON-ответов
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.post('/id/')
def create_short_link():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError(NO_REQUEST_BODY)

    if 'url' not in data:
        raise APIError(URL_REQUIRED)
    url = data['url']
    if not url:
        raise APIError(URL_REQUIRED)

    try:
        url_map = URLMap.create(url, data.get('custom_id'))
    except ValidationError as error:
        message = error.args[0] if error.args else INVALID_SHORT
        raise APIError(message) from error

    return jsonify({
        'url': url,
        'short_link': url_map.short_url
    }), HTTPStatus.CREATED


@api_bp.get('/id/<string:short>/')
def get_original_link(short):
    if (url_map := URLMap.find(short)) is None:
        raise APIError(ID_NOT_FOUND, HTTPStatus.NOT_FOUND)
    return jsonify({'url': url_map.original}), HTTPStatus.OK
