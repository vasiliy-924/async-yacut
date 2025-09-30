from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    URL,
    ValidationError
)

from yacut.constants import MAX_SHORT_ID_LENGTH, MAX_URL_LENGTH
from yacut.validators import validate_unique_short_id


class URLMapForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=(
            DataRequired(message='Обязательное поле'),
            URL(message='Введите корректный URL'),
            Length(max=MAX_URL_LENGTH),
        )
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=(
            Optional(),
            Length(1, MAX_SHORT_ID_LENGTH)
        )
    )
    submit = SubmitField('Создать')

    def validate_custom_id(self, field: StringField) -> None:
        field.data = validate_unique_short_id(
            field.data,
            require=False,
            check_unique=True,
        )


class UploadFilesForm(FlaskForm):
    files = MultipleFileField(
        validators=(FileRequired(message='Выберите хотя бы один файл'),)
    )
    submit = SubmitField('Загрузить')

    def validate_files(self, field: MultipleFileField) -> None:
        field.data = [
            file for file in (field.data or [])
            if getattr(file, 'filename', '')
        ]
        if not field.data:
            raise ValidationError('Выберите хотя бы один файл')
