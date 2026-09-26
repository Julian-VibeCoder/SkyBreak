# Builder: Python + Node für Build + DB-Init
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY skybreak/ ./skybreak/
COPY skybreak/db_migrate.py ./skybreak/db_migrate.py
COPY frontend/src/App.js ./frontend/src/App.js
COPY frontend/ ./frontend/
RUN cd frontend && npm install --prefer-offline --no-audit --no-fund && npm run build

# Final: nur Runtime
FROM python:3.11-slim
# System deps for Playwright Chromium + SQLite + Flask
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libgtk-3-0 \
    libgbm1 \
    libxshmfence1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libxrender1 \
    libdrm2 \
    libgbm-dev \
    && rm -rf /var/lib/apt/lists/*
# Install Playwright browsers in final image
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/requirements.txt .
COPY --from=builder /app/skybreak/ ./skybreak/
COPY --from=builder /app/skybreak/db_migrate.py ./skybreak/db_migrate.py

COPY --from=builder /app/frontend/build ./frontend/build

EXPOSE 80
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=skybreak/app DB_FILE=/data/skybreak.db FRONTEND_BUILD_DIR=/app/frontend/build
RUN mkdir -p /data
RUN python -m playwright install chromium
# DB init handled by container at startup (not build)
CMD ["python", "-m", "skybreak.app"]
