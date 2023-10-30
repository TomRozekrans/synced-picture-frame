FROM python:3.11.4-slim-buster
LABEL authors="tom"

RUN mkdir -p /home/app
RUN addgroup --system app && adduser --system --group app

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME $APP_HOME/staticfiles $APP_HOME/mediafiles
WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip poetry

COPY ./poetry.lock ./pyproject.toml $APP_HOME/
RUN poetry config virtualenvs.create false
RUN poetry install --only main  --no-interaction --no-ansi

COPY . $APP_HOME/
RUN chmod +x /home/app/web/entrypoint.sh

RUN chown -R app:app $APP_HOME
USER app

ENTRYPOINT ["/home/app/web/entrypoint.sh"]

