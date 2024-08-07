from flask import Flask
from config import Config
from flask_migrate import Migrate


# app.config.from_object(Config)
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    from app.models import db

    db.init_app(app)
    migrate.init_app(app, db)

    from app.api import api

    app.register_blueprint(api)
    return app


import app.models
