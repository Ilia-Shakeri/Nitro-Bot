# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_INPUT=1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        firefox-esr \
        xvfb \
        xauth \
        wget \
        ca-certificates \
        fonts-liberation \
        fonts-dejavu-core

ARG GECKODRIVER_VERSION=0.34.0
RUN --mount=type=cache,target=/root/.cache/geckodriver,sharing=locked \
    set -eux; \
    archive="/root/.cache/geckodriver/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz"; \
    if [ ! -f "$archive" ]; then \
        wget -q -O "$archive" "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz"; \
    fi; \
    tar -xzf "$archive" -C /usr/local/bin; \
    chmod +x /usr/local/bin/geckodriver

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --prefer-binary --upgrade-strategy only-if-needed -r requirements.txt

COPY . .

CMD ["python", "worker.py"]
