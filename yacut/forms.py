from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp, URL

from yacut.constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_SHORT_PATTERN,
    MAX_SHORT_LENGTH,
    MAX_URL_LENGTH,
)
from yacut.models import URLMap

# Сообщения для форм
REQUIRED_FIELD = 'Обязательное поле'
INVALID_URL = 'Введите корректный URL'
INVALID_SHORT_CHARS = 'Недопустимые символы в короткой ссылке'
SELECT_FILE = 'Выберите хотя бы один файл'
INVALID_FILE_TYPE = 'Недопустимый тип файла'

# Тексты кнопок
SUBMIT_CREATE = 'Создать'
SUBMIT_UPLOAD = 'Загрузить'


class URLMapForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=(
            DataRequired(message=REQUIRED_FIELD),
            URL(message=INVALID_URL),
            Length(max=MAX_URL_LENGTH),
        )
    )
    short = StringField(
        'Ваш вариант короткой ссылки',
        validators=(
            Optional(),
            Length(max=MAX_SHORT_LENGTH),
            Regexp(ALLOWED_SHORT_PATTERN, message=INVALID_SHORT_CHARS),
        )
    )
    submit = SubmitField(SUBMIT_CREATE)

    def validate_short(self, field: StringField) -> None:
        field.data = URLMap.validate_short(
            field.data,
            require=False,
            check_unique=True,
        )


class UploadFilesForm(FlaskForm):
    files = MultipleFileField(
        validators=(
            FileRequired(message=SELECT_FILE),
            FileAllowed(ALLOWED_EXTENSIONS, message=INVALID_FILE_TYPE),
        )
    )
    submit = SubmitField(SUBMIT_UPLOAD)
