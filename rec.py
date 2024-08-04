from datetime import datetime, timedelta
import sqlalchemy.orm as so
import sqlalchemy as sa
from werkzeug.exceptions import HTTPException

from app.app import create_app
from app.api.error import error_response
from app.models import User, Restaurant, Table, Restriction, db

app = create_app()


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Catch-all error handler to return JSON instead of HTML"""
    return error_response(e.code)


@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "so": so,
        "db": db,
        "User": User,
        "Restaurant": Restaurant,
        "Table": Table,
        "Restriction": Restriction,
        "datetime": datetime,
        "timedelta": timedelta,
    }
