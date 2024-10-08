# Stage 1 - Compile Python dependencies
FROM python:3.12-slim-bullseye AS compile-image

# create and use virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Add and install build dependencies
COPY requirements.txt .
RUN pip install --upgrade pip pip-tools

# Sync virtual env with app's dependencies
RUN pip-sync requirements.txt

# Stage 2 - Build docker image suitable for deployment
FROM python:3.12-slim-bullseye AS runtime-image

# copy python dependencies
COPY --from=compile-image /opt/venv /opt/venv

WORKDIR /app

# add application
COPY . /app

EXPOSE 8000

## set environment variables
ENV PATH="/opt/venv/bin:$PATH"

## start the application
CMD ["gunicorn", "-c", "python:src.config.gunicorn", "src.app:create_app()"]
