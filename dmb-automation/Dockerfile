# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System deps: Firefox (real browser), Xvfb (virtual display), fonts, and tools to
# fetch geckodriver. Xvfb lets the JS/Vue-heavy DMB site render exactly as in a real
# browser, avoiding headless-mode quirks.
RUN apt-get update && apt-get install -y --no-install-recommends \
        firefox-esr \
        xvfb \
        xauth \
        wget \
        ca-certificates \
        fonts-liberation \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Pinned geckodriver — reproducible builds, compatible with Firefox ESR + Selenium 4.18.
ARG GECKODRIVER_VERSION=0.34.0
RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && tar -xzf "geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" -C /usr/local/bin \
    && rm "geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && chmod +x /usr/local/bin/geckodriver

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .

CMD ["python", "worker.py"]
