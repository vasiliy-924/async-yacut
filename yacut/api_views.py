from http import HTTPStatus

from flask import Blueprint, jsonify, request
from wtforms import ValidationError

from yacut.error_handlers import APIError
from yacut.models import DUPLICATE_SHORT, INVALID_SHORT, URLMap


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.post('/id/')
def create_short_link():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError('Отсутствует тело запроса')

    url = data.get('url')
    if not url:
        raise APIError('"url" является обязательным полем!')

    # Поддержка обоих форматов для обратной совместимости
    short_input = (
        data.get('short') or data.get('custom_id')
        if isinstance(data, dict) else None
    )

    try:
        short = URLMap.validate_short(
            short_input,
            require=False,
            check_unique=True,
        )
    except ValidationError as error:
        message = error.args[0] if error.args else INVALID_SHORT
        raise APIError(message) from error

    if not short:
        short = URLMap.get_unique_short()

    try:
        url_map = URLMap.create(url, short)
    except Exception as exc:
        raise APIError(DUPLICATE_SHORT) from exc

    short_url = url_map.get_short_url()
    return jsonify({
        'url': url,
        'short_url': short_url,
        'short_link': short_url  # Для обратной совместимости
    }), HTTPStatus.CREATED


@api_bp.get('/id/<string:short>/')
def get_original_link(short):
    url_map = URLMap.find_by_short(short)
    if url_map is None:
        raise APIError('Указанный id не найден', HTTPStatus.NOT_FOUND)
    return jsonify({'url': url_map.original}), HTTPStatus.OK
