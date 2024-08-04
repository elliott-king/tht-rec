import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Hardcoded for simplicity, it's only MySQL
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
