FROM python:3.12-slim

# Mirror overrides for regions where debian/pypi defaults are slow or
# unreachable (set APT_MIRROR / PIP_INDEX_URL in .env; defaults keep
# upstream behavior).
ARG APT_MIRROR=http://deb.debian.org
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

# curl is used by the container health check.
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|http://deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install runtime dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/logs

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v2/health || exit 1

# Use factory pattern for create_app
CMD ["uvicorn", "main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
