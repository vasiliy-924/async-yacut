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
MSG_SHORT_LINK_CREATED = 'Короткая ссылка успешно создана!'
MSG_FILES_UPLOADED = 'Файлы успешно загружены на Яндекс Диск.'
MSG_FILE_READ_ERROR = 'Ошибка при чтении файлов.'


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLMapForm()
    short_url = None

    if form.is_submitted() and not form.validate():
        for errors in form.errors.values():
            for message in errors:
                flash(message, FLASH_DANGER)
    elif form.validate_on_submit():
        short = form.custom_id.data or URLMap.get_unique_short()
        url_map = URLMap.create(form.original_link.data, short)
        short_url = url_map.get_short_url()
        flash(MSG_SHORT_LINK_CREATED, FLASH_SUCCESS)

    return render_template(
        TEMPLATE_INDEX,
        form=form,
        short_url=short_url,
        active_page=PAGE_INDEX,
    )


@app.route('/files', methods=['GET', 'POST'])
def files_view():
    form = UploadFilesForm()
    uploaded_items = []

    # Early return: сначала проверяем условия, дающие ранний возврат
    if not form.validate_on_submit():
        if form.is_submitted():
            for errors in form.errors.values():
                for message in errors:
                    flash(message, FLASH_DANGER)
        return render_template(
            TEMPLATE_FILES,
            form=form,
            uploaded_items=uploaded_items,
            active_page=PAGE_FILES,
        )

    # Часть 1: Преобразование набора файлов в FileToUpload
    # (вынесено в services)
    try:
        files_to_upload = prepare_files_for_upload(form.files.data)
    except Exception:
        flash(MSG_FILE_READ_ERROR, FLASH_DANGER)
        return render_template(
            TEMPLATE_FILES,
            form=form,
            uploaded_items=uploaded_items,
            active_page=PAGE_FILES,
        )

    # Часть 2: Загрузка файлов на Яндекс Диск и получение урлов
    try:
        uploaded_files = upload_files_to_yandex_disk(
            files_to_upload,
            token=current_app.config.get('DISK_TOKEN'),
        )
    except YandexDiskServiceError as error:
        flash(str(error), FLASH_DANGER)
        return render_template(
            TEMPLATE_FILES,
            form=form,
            uploaded_items=uploaded_items,
            active_page=PAGE_FILES,
        )

    # Часть 3: Преобразование урлов в URLMap через list comprehension
    if uploaded_files:
        url_maps = [
            URLMap.create(result.original_url, result.short, commit=False)
            for result in uploaded_files
        ]
        db.session.commit()

        uploaded_items = [
            {
                'filename': result.filename,
                'link': url_map.get_short_url(),
            }
            for result, url_map in zip(uploaded_files, url_maps)
        ]
        flash(MSG_FILES_UPLOADED, FLASH_SUCCESS)

    return render_template(
        TEMPLATE_FILES,
        form=form,
        uploaded_items=uploaded_items,
        active_page=PAGE_FILES,
    )


@app.route('/<string:short>')
def redirect_view(short):
    url_map = URLMap.find_by_short(short)
    if url_map is None:
        abort(HTTPStatus.NOT_FOUND)
    return redirect(url_map.original)


@app.route('/docs/')
def swagger_ui():
    """Отображение Swagger UI документации"""
    return render_template('swagger.html')


@app.route('/openapi.json')
def openapi_json():
    """Отдача OpenAPI спецификации в формате JSON"""
    try:
        # Путь к файлу openapi.yml
        spec_path = os.path.join(current_app.root_path, 'openapi.yml')
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
        return jsonify(spec)
    except Exception as e:
        current_app.logger.error(f"Ошибка загрузки OpenAPI спецификации: {e}")
        return jsonify({"error": "Не удалось загрузить спецификацию"}), 500
