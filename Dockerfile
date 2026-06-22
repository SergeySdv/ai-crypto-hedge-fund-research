# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONUNBUFFERED=1 \
    UV_HTTP_TIMEOUT=300 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    XDG_CACHE_HOME=/tmp/.cache

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git make \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

CMD ["make", "release-verify"]
