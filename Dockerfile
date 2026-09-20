FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Build React frontend
COPY frontend/package.json frontend/src/ ./frontend/
RUN cd frontend && npm install && npm run build || echo "React build attempted"
# App + DB init
COPY init_db.py .
COPY skybreak/ ./skybreak/
RUN pip install --no-cache-dir flask pytest && python init_db.py
COPY . .
# SQLite DB path in container (mount target)
RUN mkdir -p /data
# Serve on port 80 via Flask
EXPOSE 80
CMD ["python", "-m", "flask", "--app", "skybreak/app", "run", "--host=0.0.0.0", "--port=80"]
