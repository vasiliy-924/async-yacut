from flask_wtf import FlaskForm
from wtforms import URLField
from wtforms.validators import Length

class URLMapForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[Length(1, 256)]
    )
    custom_id = URL_Field(
        'Ваш вариант короткой ссылки',
        validators=[Length(1, 128)]
    )
