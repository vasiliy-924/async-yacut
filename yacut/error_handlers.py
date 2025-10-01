from http import HTTPStatus

from flask import jsonify, render_template, request

from yacut import app, db


class APIError(Exception):
    """Исключение для API с автоматическим откатом транзакции."""

    def __init__(self, message, status_code=HTTPStatus.BAD_REQUEST):
        super().__init__()
        self.message = message
        self.status_code = status_code


@app.errorhandler(APIError)
def handle_api_error(error):
    """Обработчик API-исключений с откатом транзакции."""
    db.session.rollback()
    return jsonify({'message': error.message}), error.status_code


@app.errorhandler(HTTPStatus.NOT_FOUND)
def page_not_found(error):
    default_message = 'Страница не найдена.'
    message = getattr(error, 'description', default_message)
    if request.path.startswith('/api/'):
        return jsonify({'message': message}), HTTPStatus.NOT_FOUND
    return (
        render_template('404.html', message=default_message),
        HTTPStatus.NOT_FOUND,
    )


@app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def internal_error(error):
    db.session.rollback()
    description = 'Внутренняя ошибка сервера.'
    if request.path.startswith('/api/'):
        return (
            jsonify({'message': description}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    return (
        render_template('500.html', message=description),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
