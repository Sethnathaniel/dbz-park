FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

# Dependencies first: this layer is reused as long as the lockfile does not change.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE 8000
# Migrate, then serve: a fresh database is ready before the first request.
CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --port 8000"]
