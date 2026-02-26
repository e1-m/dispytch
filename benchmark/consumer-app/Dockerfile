FROM python:3.13-slim-bookworm
LABEL authors="e1_m"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    g++ && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
USER appuser
WORKDIR /app

RUN curl -fsSL https://astral.sh/uv/install.sh | sh

ENV PATH="/home/appuser/.local/bin:$PATH"
COPY pyproject.toml uv.lock README.md ./
COPY dispytch ./dispytch

RUN uv sync --no-group docs --extra kafka

WORKDIR /app/test

COPY ./benchmark/consumer-app/src src

CMD ["./../.venv/bin/python", "-m", "src.main"]




