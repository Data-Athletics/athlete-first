# check=skip=UndefinedVar
FROM python:3.14.2 AS base

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:/scripts:$PATH"
ENV PYTHONPATH="/scripts:/app:$PYTHONPATH"

USER root

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

WORKDIR /app

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Move pyproject.toml to working dir
COPY pyproject.toml uv.lock ./

FROM base AS dev
ENV UV_NO_DEV=0

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-editable --no-install-project --extra server --extra dev

COPY ./app /app/app 
COPY ./scripts /scripts

# Sync project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra server --extra dev

CMD ["/scripts/entrypoint.sh", "dev"]

FROM base AS prod
ENV UV_NO_DEV=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-editable --no-install-project --extra server

COPY ./app /app/app 
COPY ./scripts /scripts 

# Sync project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra server

CMD ["/scripts/entrypoint.sh", "prod"]
