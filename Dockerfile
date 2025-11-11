# dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

# Install build deps only when needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project first so we can conditionally install deps
COPY . .

# Install Python dependencies only if `requirements.txt` exists
RUN if [ -f requirements.txt ]; then \
      echo "found requirements.txt, installing dependencies..." && \
      pip install --upgrade pip --disable-pip-version-check && \
      pip install --no-cache-dir -r requirements.txt; \
    else \
      echo "no requirements.txt found, skipping pip install"; \
    fi

# Create non-root user and set ownership
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0"]