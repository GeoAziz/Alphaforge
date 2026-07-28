# ==========================================================================
# Stage 1: Build dependencies
# ==========================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================================================
# Stage 2: Production image
# ==========================================================================
FROM python:3.11-slim AS production

# Security: run as non-root
RUN groupadd -r alphaforge && useradd -r -g alphaforge -d /app -s /sbin/nologin alphaforge

# Install system deps needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create directories for runtime
RUN mkdir -p /app/logs /app/tmp /app/data && \
    chown -R alphaforge:alphaforge /app

USER alphaforge

EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
# NOTE: FORWARD_PROXY_IPS controls which IPs are trusted for X-Forwarded-For.
# Set to your reverse proxy IP(s) in production. Only use "*" for local dev.
# Example: FORWARD_PROXY_IPS=172.28.0.1,10.0.0.1
CMD ["sh", "-c", "uvicorn main:app \
     --host 0.0.0.0 \
     --port 8000 \
     --workers 4 \
     --loop uvloop \
     --http httptools \
     --log-level info \
     --access-log \
     --proxy-headers \
     --forwarded-allow-ips ${FORWARD_PROXY_IPS:-127.0.0.1}"]
