FROM python:3.12-slim AS base

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=".:./src"
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip3 install --no-cache-dir poetry


FROM base AS dependencies

# Copy only dependency files
COPY pyproject.toml poetry.lock ./

RUN chmod 644 pyproject.toml poetry.lock

RUN poetry config --local virtualenvs.create false
RUN POETRY_REQUESTS_TIMEOUT=300 poetry install --no-interaction --no-ansi --no-root


FROM dependencies AS app

RUN addgroup --system appgroup && adduser --system --group appuser

# Copy application code
COPY . .

RUN chown -R appuser:appgroup /app
RUN chmod +x entrypoint.sh

USER appuser

# Expose port (can be overridden)
ARG PORT=8000
EXPOSE ${PORT}

# Run entrypoint
CMD ["./entrypoint.sh"]
