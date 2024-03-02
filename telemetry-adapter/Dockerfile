FROM python:3.12.2-slim
LABEL authors="Andrey Arakelyants"

RUN apt update
RUN apt install -y pipx
RUN pipx ensurepath
RUN pipx install poetry==1.8.0

WORKDIR /telemetry-adapter
COPY . .
RUN ~/.local/bin/poetry install --no-root

ENTRYPOINT ["python", "main.py"]