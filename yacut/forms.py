from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL

from yacut.validators import validate_unique_short_id


class URLMapForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            URL(message='Введите корректный URL'),
            Length(max=2048),
        ]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[
            Optional(),
            Length(1, 64)
        ]
    )
    submit = SubmitField('Создать')

    def validate_custom_id(self, field: StringField) -> None:
        field.data = validate_unique_short_id(field.data)


class UploadFilesForm(FlaskForm):
    files = MultipleFileField(
        validators=[FileRequired(message='Выберите хотя бы один файл')]
    )
    submit = SubmitField('Загрузить')
