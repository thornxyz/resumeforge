# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder

WORKDIR /app

COPY --chown=uv:uv pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/home/uv/.cache/uv \
	uv sync --frozen --no-dev

COPY --chown=uv:uv . .
RUN --mount=type=cache,target=/home/uv/.cache/uv \
	uv sync --frozen --no-dev

FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS runtime

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uv", "run", "main.py"]
