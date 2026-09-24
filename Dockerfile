# Builder: Python + Node für Build + DB-Init
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY skybreak/ ./skybreak/
COPY init_db.py ./init_db.py
COPY frontend/ ./frontend/
RUN cd frontend && npm install --prefer-offline --no-audit --no-fund && npm run build

# Final: nur Runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/requirements.txt .
COPY --from=builder /app/skybreak/ ./skybreak/
COPY --from=builder /app/init_db.py ./init_db.py

COPY --from=builder /app/frontend/build ./frontend/build

EXPOSE 80
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=skybreak/app DB_FILE=/data/skybreak.db FRONTEND_BUILD_DIR=/app/frontend/build
RUN mkdir -p /data
# DB init handled by container at startup (not build)
CMD ["python", "-m", "skybreak.app"]
