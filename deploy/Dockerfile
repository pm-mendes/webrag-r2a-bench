# Bench image. Build from the repository root with `make image` so that the bench
# version is captured (there is no .git directory inside the image).
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /bench

# dependencies first, from the lock file only (cached layer)
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev

COPY config ./config
COPY corpus ./corpus
COPY schemas ./schemas

ARG BENCH_VERSION
RUN test -n "$BENCH_VERSION" || (echo "BENCH_VERSION build argument is required" && exit 1)
ENV WEBRAG_BENCH_VERSION=${BENCH_VERSION} \
    PATH="/bench/.venv/bin:${PATH}"

RUN useradd --create-home --uid 1000 bench && mkdir -p /bench/runs && chown bench /bench/runs
USER bench

ENTRYPOINT ["webrag-bench"]
CMD ["--help"]
