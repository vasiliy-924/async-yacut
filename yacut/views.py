from flask import abort, current_app, redirect, render_template, url_for

from yacut import app, db
from yacut.forms import UploadFilesForm, URLMapForm
from yacut.models import URLMap
from yacut.services import (
    FileToUpload,
    YandexDiskServiceError,
    get_unique_short_id,
    upload_files_to_yandex_disk,
)
from yacut.constants import HTTP_STATUS_NOT_FOUND


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLMapForm()
    short_link = None

    if form.validate_on_submit():
        short_id = form.custom_id.data or get_unique_short_id()
        url_map = URLMap(original=form.original_link.data, short=short_id)
        db.session.add(url_map)
        db.session.commit()
        short_link = url_for(
            'redirect_view', short_id=short_id, _external=True)

    return render_template(
        'make_link_short.html',
        form=form,
        short_link=short_link,
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
            form.files.errors.append(str(error))
        else:
            if uploaded_files:
                for result in uploaded_files:
                    url_map = URLMap(
                        original=result.original_url,
                        short=result.short_id,
                    )
                    db.session.add(url_map)
                db.session.commit()
                uploaded_items = tuple(
                    {
                        'filename': result.filename,
                        'link': url_for(
                            'redirect_view',
                            short_id=result.short_id,
                            _external=True,
                        ),
                    }
                    for result in uploaded_files
                )

    return render_template(
        'load_foles.html',
        form=form,
        uploaded_items=uploaded_items,
        active_page='files',
    )


@app.route('/<string:short_id>')
def redirect_view(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if url_map is None:
        abort(HTTP_STATUS_NOT_FOUND)
    return redirect(url_map.original)