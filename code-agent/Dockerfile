FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app

COPY --chown=uv:uv pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/home/uv/.cache/uv \
	uv sync --frozen --no-dev

COPY --chown=uv:uv . .

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS runtime
WORKDIR /app

# Ensure runtime has an `uv` user available for non-root execution
RUN groupadd --system uv \
	&& useradd --system --gid uv --create-home uv

COPY --from=builder /app /app

# Ensure you are running as uv user (if required)
USER uv

ENV PATH="/app/.venv/bin:${PATH}" \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uv", "run", "main.py"]
