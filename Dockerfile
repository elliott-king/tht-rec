FROM --platform=linux/amd64 python:3.12-bullseye

# Install deps
COPY pyproject.toml poetry.lock ./
RUN pip install poetry --progress-bar off
RUN pip install gunicorn --progress-bar off
RUN poetry install --no-interaction --no-ansi

ENV FLASK_APP=rec.py

COPY migrations migrations
COPY app app
COPY rec.py .
COPY scripts.py .
COPY config.py .

# Seed db
RUN poetry run flask db upgrade
RUN poetry run python scripts.py

# Runs on port 5000 by default
EXPOSE 5000
CMD [ "poetry", "run", "python", "-m", "flask", "run", "--host=0.0.0.0" ]