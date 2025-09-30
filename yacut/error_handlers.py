from flask import jsonify, render_template, request

from yacut import app
from yacut.constants import HTTP_STATUS_INTERNAL_ERROR, HTTP_STATUS_NOT_FOUND


@app.errorhandler(HTTP_STATUS_NOT_FOUND)
def page_not_found(error):
    default_message = 'Страница не найдена.'
    message = getattr(error, 'description', default_message)
    if request.path.startswith('/api/'):
        return jsonify({'message': message}), HTTP_STATUS_NOT_FOUND
    return (
        render_template('404.html', message=default_message),
        HTTP_STATUS_NOT_FOUND,
    )


@app.errorhandler(HTTP_STATUS_INTERNAL_ERROR)
def internal_error(error):
    description = 'Внутренняя ошибка сервера.'
    if request.path.startswith('/api/'):
        return jsonify({'message': description}), HTTP_STATUS_INTERNAL_ERROR
    return (
        render_template('500.html', message=description),
        HTTP_STATUS_INTERNAL_ERROR,
    )
