FROM python:3.8-slim-buster

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

ADD src/requirements/ /tmp/

RUN apt-get update \
  && apt-get install -y \
    build-essential \
    binutils \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-cffi \
    libxslt-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libpq-dev \
    libjpeg-dev \
    libgdal-dev \
    wkhtmltopdf

RUN pip3 install --no-cache-dir  -r /tmp/dev.txt

RUN groupadd -g 1000 www
RUN useradd -u 1000 -ms /bin/bash -g www www
