FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_DOWNLOADS=0
ENV UV_LINK_MODE=copy

WORKDIR /app/bg_workers

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*


COPY bg_workers/pyproject.toml bg_workers/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-install-local --no-editable

COPY shared /app/shared
COPY bg_workers /app/bg_workers

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/bg_workers

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/bg_workers /app/bg_workers

ENV PATH="/app/bg_workers/.venv/bin:$PATH"


