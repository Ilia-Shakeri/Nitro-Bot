# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_INPUT=1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        firefox-esr \
        wget \
        ca-certificates \
        fonts-liberation \
        fonts-dejavu-core

ARG GECKODRIVER_VERSION=0.37.1
ARG TARGETARCH
RUN --mount=type=cache,target=/root/.cache/geckodriver,sharing=locked \
    set -eux; \
    case "${TARGETARCH}" in \
        amd64) platform="linux64"; sha256="e815130ea95983e162ae91843b48d3a3ce991735635fce83a647afde21e09f7e" ;; \
        arm64) platform="linux-aarch64"; sha256="8fd90b951422fbad5b56539fb344dff66eb3f986d615d8d6fde9f1f62dad610c" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    archive="/root/.cache/geckodriver/geckodriver-v${GECKODRIVER_VERSION}-${platform}.tar.gz"; \
    if [ ! -f "$archive" ]; then \
        wget -q -O "$archive" "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${platform}.tar.gz"; \
    fi; \
    echo "${sha256}  ${archive}" | sha256sum -c -; \
    tar -xzf "$archive" -C /usr/local/bin; \
    chmod +x /usr/local/bin/geckodriver

WORKDIR /app

COPY dmb-automation/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --prefer-binary --upgrade-strategy only-if-needed -r requirements.txt

COPY dmb-automation/ .
COPY shared/ /shared/

CMD ["python", "worker.py"]
