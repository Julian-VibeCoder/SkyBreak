# Builder: Python + Node für Build + DB-Init
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY init_db.py skybreak/ ./
RUN python init_db.py
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build || echo "build attempted"

# Final: nur Runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/skybreak/ ./skybreak/
COPY --from=builder /app/init_db.py .
COPY --from=builder /app/skybreak.db .
COPY --from=builder /app/frontend/build ./frontend/build

RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true
EXPOSE 8000
ENV FLASK_APP=skybreak/app
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]
