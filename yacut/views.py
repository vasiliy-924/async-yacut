from random import randrange

from flask import render_template

from yacut import app, db
from yacut.forms import URLMapForm
from yacut.models import URLMap


@app.route('/')
def index_view():
    return render_template('index.html')