FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
COPY . /code/

# Install *this* package in editable mode. If we then mount the 'massmigration' folder as a volume
# when running the Docker container, it should pick up local changes to the files.
RUN pip install -e .
COPY . /code/

ENV DJANGO_SETTINGS_MODULE "testing.test_settings"

ENTRYPOINT ["./testing/docker_entrypoint.sh"]
