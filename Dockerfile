FROM python:3.13.1

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        biber \
        latexmk \
        texlive-full && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /opt/lunabot

COPY pyproject.toml .
COPY .python-version .

RUN uv sync --locked

COPY bot ./bot

COPY main.py .

CMD ["uv", "run", "main.py"]
