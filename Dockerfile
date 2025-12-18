FROM ubuntu:latest

# 1. Install system dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# 2. Install Poetry (official recommended way)
RUN curl -sSL https://install.python-poetry.org | python3 -

# 3. Set environment so poetry is on PATH, avoid virtualenv in Docker
ENV PATH="/root/.local/bin:$PATH"
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# 4. Copy only dependency files first for better Docker caching
COPY pyproject.toml poetry.lock* /app/

# 5. Install dependencies (no virtualenv)
RUN poetry install --no-root

# 6. Copy project code
COPY . /app

EXPOSE 9000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000"]
