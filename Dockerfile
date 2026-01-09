FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (none needed strictly for pure python, but good practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy poetry config
COPY pyproject.toml poetry.lock ./

# Install dependencies
# We do not create a virtualenv inside Docker, we install to system python or
# we can use poetry to create one. System python is simpler for docker.
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy app code
COPY src/ ./src/
COPY config/ ./config/

CMD ["python", "-m", "src.bot"]
