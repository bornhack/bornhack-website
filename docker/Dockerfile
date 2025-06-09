FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

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

ADD pyproject.toml /app/
ADD README.md /app/
ADD src /app/src/

RUN uv pip install --system --no-cache-dir .[dev,test]

RUN rm -rf /app/*

RUN groupadd -g 1000 www
RUN useradd -u 1000 -ms /bin/bash -g www www
