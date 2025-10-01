from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from settings import Config


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from yacut.api_views import api_bp  # noqa: E402
from yacut import error_handlers, views  # noqa: F401


app.register_blueprint(api_bp)
