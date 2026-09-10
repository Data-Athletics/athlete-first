FROM python:3.14.2 AS BASE

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-install-project

ENV PATH="/app/.venv/bin:$PATH"


FROM BASE AS DEV

WORKDIR /app

CMD [ "python", "app/main.py" ]


FROM BASE AS TEST

CMD [ "pytest" ]


FROM BASE AS PROD

COPY . .

CMD [ "python", "app/main.py" ]