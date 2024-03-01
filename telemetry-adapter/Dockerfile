FROM python:3.12.2-bookworm
LABEL authors="Andrey Arakelyants"

WORKDIR /telemetry-adapter
COPY . .
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN ~/.local/share/pypoetry/venv/bin/poetry install --no-root

ENTRYPOINT ["python", "main.py"]