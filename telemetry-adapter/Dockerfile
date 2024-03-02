FROM python:3.12.2-slim
LABEL authors="Andrey Arakelyants"

#RUN apt update
#RUN apt install -y pipx
#RUN pipx ensurepath
#RUN pipx install poetry==1.8.0
RUN apt update
RUN apt install -y curl
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /telemetry-adapter
COPY . .
RUN poetry install --no-root

RUN chmod u+x run.sh