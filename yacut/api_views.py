from flask import Blueprint, jsonify, request, url_for
from wtforms import ValidationError

from yacut import db
from yacut.constants import (
    DUPLICATE_SHORT_ID_MSG,
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_CREATED,
    HTTP_STATUS_NOT_FOUND,
    HTTP_STATUS_OK,
    INVALID_SHORT_ID_MSG,
)
from yacut.models import URLMap
from yacut.services import get_unique_short_id
from yacut.validators import validate_unique_short_id


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.post('/id/')
def create_short_link():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return (
            jsonify({'message': 'Отсутствует тело запроса'}),
            HTTP_STATUS_BAD_REQUEST,
        )

    url = data.get('url')
    if not url:
        return (
            jsonify({'message': '"url" является обязательным полем!'}),
            HTTP_STATUS_BAD_REQUEST,
        )

    custom_id = data.get('custom_id') if isinstance(data, dict) else None

    try:
        short_id = validate_unique_short_id(
            custom_id,
            require=False,
            check_unique=True,
        )
    except ValidationError as error:
        message = error.args[0] if error.args else INVALID_SHORT_ID_MSG
        return jsonify({'message': message}), HTTP_STATUS_BAD_REQUEST

    if not short_id:
        short_id = get_unique_short_id()

    url_map = URLMap(original=url, short=short_id)
    db.session.add(url_map)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return (
            jsonify({'message': DUPLICATE_SHORT_ID_MSG}),
            HTTP_STATUS_BAD_REQUEST,
        )

    short_link = url_for('redirect_view', short_id=short_id, _external=True)
    return jsonify({'url': url, 'short_link': short_link}), HTTP_STATUS_CREATED


@api_bp.get('/id/<string:short_id>/')
def get_original_link(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if url_map is None:
        return (
            jsonify({'message': 'Указанный id не найден'}),
            HTTP_STATUS_NOT_FOUND,
        )
    return jsonify({'url': url_map.original}), HTTP_STATUS_OK
