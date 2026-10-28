# Builder: Python + Node für Build + DB-Init
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY skybreak/ ./skybreak/
COPY frontend/ ./frontend/
RUN cd frontend && npm ci --no-audit --no-fund && npm run build

# Final: nur Runtime
FROM python:3.11-slim
WORKDIR /app
# libsqlite3-0 is the only native runtime dep (Python's sqlite3 binds to it).
# No GTK/Chromium/Playwright libs are needed at runtime: they were only ever used
# by tests; the price scraper uses primp+selectolax (pure HTTP).
RUN apt-get update && apt-get install -y --no-install-recommends libsqlite3-0 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/requirements.txt .
COPY --from=builder /app/skybreak/ ./skybreak/
COPY --from=builder /app/frontend/build ./frontend/build

EXPOSE 80
ENV PYTHONUNBUFFERED=1
ENV DB_FILE=/data/skybreak.db FRONTEND_BUILD_DIR=/app/frontend/build
RUN mkdir -p /data
# DB schema is created/migrated at container startup, not at build time.
CMD ["python", "-m", "skybreak.app"]
