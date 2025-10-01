from http import HTTPStatus

from flask import abort, current_app, flash, redirect, render_template

from yacut import app, db
from yacut.forms import UploadFilesForm, URLMapForm
from yacut.models import URLMap
from yacut.services import (
    FileToUpload,
    YandexDiskServiceError,
    upload_files_to_yandex_disk,
)


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLMapForm()
    short_url = None

    if form.validate_on_submit():
        short = form.short.data or URLMap.get_unique_short()
        url_map = URLMap.create(form.original_link.data, short)
        short_url = url_map.get_short_url()
        flash('Короткая ссылка успешно создана!', 'success')
    elif form.is_submitted():
        for errors in form.errors.values():
            for message in errors:
                flash(message, 'danger')

    return render_template(
        'index.html',
        form=form,
        short_url=short_url,
        active_page='index',
    )


@app.route('/files', methods=['GET', 'POST'])
def files_view():
    form = UploadFilesForm()
    uploaded_items = []

    if form.validate_on_submit():
        files_to_upload = []
        for storage in form.files.data:
            content = storage.read()
            files_to_upload.append(
                FileToUpload(filename=storage.filename, content=content)
            )

        try:
            uploaded_files = upload_files_to_yandex_disk(
                files_to_upload,
                token=current_app.config.get('DISK_TOKEN'),
            )
        except YandexDiskServiceError as error:
            message = str(error)
            form.files.errors.append(message)
            flash(message, 'danger')
        else:
            if uploaded_files:
                url_maps = [
                    URLMap.create(
                        result.original_url,
                        result.short,
                        commit=False
                    )
                    for result in uploaded_files
                ]
                db.session.commit()
                uploaded_items = tuple(
                    {
                        'filename': result.filename,
                        'link': url_map.get_short_url(),
                    }
                    for result, url_map in zip(uploaded_files, url_maps)
                )
                flash('Файлы успешно загружены на Яндекс Диск.', 'success')
    elif form.is_submitted():
        for errors in form.errors.values():
            for message in errors:
                flash(message, 'danger')

    return render_template(
        'load_files.html',
        form=form,
        uploaded_items=uploaded_items,
        active_page='files',
    )


@app.route('/<string:short>')
def redirect_view(short):
    url_map = URLMap.find_by_short(short)
    if url_map is None:
        abort(HTTPStatus.NOT_FOUND)
    return redirect(url_map.original)