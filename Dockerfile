# KEV System One API (default: kev-0.8b on CPU, port 8009)
#
# From this repo:
#   docker compose up --build -d
#   curl -s http://127.0.0.1:8009/v1/models

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /opt/kev

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Project sources (pyproject + kev package)
COPY pyproject.toml uv.lock README.md ./
COPY kev ./kev
COPY docker/kev_entrypoint.py /opt/kev/docker/kev_entrypoint.py

RUN uv sync --extra serve

ENV HF_HOME=/models \
    KEV_HOST=0.0.0.0 \
    KEV_MODEL_RUN=jaredpalmer/kev-0.8b

EXPOSE 8009

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD curl -fsS "http://127.0.0.1:8009/v1/models" || exit 1

CMD ["sh", "-c", "uv run --extra serve python /opt/kev/docker/kev_entrypoint.py --run \"${KEV_MODEL_RUN}\" --port 8009 --host \"${KEV_HOST}\""]
