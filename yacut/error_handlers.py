from flask import jsonify, render_template, request

from yacut import app


@app.errorhandler(404)
def page_not_found(error):
    default_message = 'Страница не найдена.'
    message = getattr(error, 'description', default_message)
    if request.path.startswith('/api/'):
        return jsonify({'message': message}), 404
    return render_template('404.html', message=default_message), 404


@app.errorhandler(500)
def internal_error(error):
    description = 'Внутренняя ошибка сервера.'
    if request.path.startswith('/api/'):
        return jsonify({'message': description}), 500
    return render_template('500.html', message=description), 500

