FROM python:3.11-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.3.2

# System deps:
RUN pip install "poetry==$POETRY_VERSION"
RUN apt-get -y update
RUN apt-get install -y ffmpeg

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY pyproject.toml ./

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY selfhostNoReplitDB.py ./
COPY docker-entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Change this env var with your discord token
ENV token ""
ENTRYPOINT ["/entrypoint.sh"]