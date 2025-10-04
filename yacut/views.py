from http import HTTPStatus
import os
import yaml

from flask import abort, current_app, flash, redirect, render_template, jsonify

from yacut import app, db
from yacut.forms import UploadFilesForm, URLMapForm
from yacut.models import URLMap
from yacut.services import (
    YandexDiskServiceError,
    prepare_files_for_upload,
    upload_files_to_yandex_disk,
)

# Шаблоны
TEMPLATE_INDEX = 'index.html'
TEMPLATE_FILES = 'load_files.html'

# Имена страниц для активной навигации
PAGE_INDEX = 'index'
PAGE_FILES = 'files'

# Категории flash-сообщений
FLASH_DANGER = 'danger'
FLASH_SUCCESS = 'success'

# Сообщения для пользователя
SHORT_LINK_CREATED = 'Короткая ссылка успешно создана!'
FILES_UPLOADED = 'Файлы успешно загружены на Яндекс Диск.'
FILE_READ_ERROR = 'Ошибка при чтении файлов.'
SHORT_LINKS_CREATION_ERROR = 'Ошибка при создании коротких ссылок'


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLMapForm()
    short_url = None

    if not form.validate():
        return render_template(
            TEMPLATE_INDEX,
            form=form,
            short_url=short_url,
            active_page=PAGE_INDEX,
        )

    try:
        short_url = URLMap.create(
            form.original_link.data,
            form.custom_id.data,
            validate=False
        ).get_short_url()
    except Exception:
        flash(SHORT_LINKS_CREATION_ERROR, FLASH_DANGER)
        return render_template(
            TEMPLATE_INDEX,
            form=form,
            short_url=None,
            active_page=PAGE_INDEX,
        )

    return render_template(
        TEMPLATE_INDEX,
        form=form,
        short_url=short_url,
        active_page=PAGE_INDEX,
    )


@app.route('/files', methods=['GET', 'POST'])
def files_view():
    form = UploadFilesForm()

    if not form.validate_on_submit():
        return render_template(
            TEMPLATE_FILES,
            form=form,
            active_page=PAGE_FILES,
        )

    # Часть 1-2: Преобразование файлов и загрузка на Яндекс Диск
    try:
        uploaded_files = upload_files_to_yandex_disk(
            prepare_files_for_upload(form.files.data),
        )
    except YandexDiskServiceError as error:
        flash(str(error), FLASH_DANGER)
        return render_template(
            TEMPLATE_FILES,
            form=form,
            active_page=PAGE_FILES,
        )

    # Часть 3: Преобразование урлов в URLMap через list comprehension
    try:
        uploaded_items = (
            {
                'filename': result.filename,
                'link': URLMap.create(
                    result.original_url,
                    result.short,
                    commit=False,
                    validate=False
                ).get_short_url(),
            }
            for result in uploaded_files
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(SHORT_LINKS_CREATION_ERROR, FLASH_DANGER)

        return render_template(
            TEMPLATE_FILES,
            form=form,
            active_page=PAGE_FILES
        )

    return render_template(
        TEMPLATE_FILES,
        form=form,
        uploaded_items=uploaded_items,
        active_page=PAGE_FILES,
    )


@app.route('/<string:short>')
def redirect_view(short):
    if (url_map := URLMap.find(short)) is None:
        abort(HTTPStatus.NOT_FOUND)
    return redirect(url_map.original)


@app.route('/docs/')
def swagger_ui():
    """Отображение Swagger UI документации"""
    return render_template('swagger.html')


@app.route('/openapi.json')
def openapi_json():
    """Отдача OpenAPI спецификации в формате JSON"""
    spec_path = os.path.join(current_app.root_path, 'openapi.yml')
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)
