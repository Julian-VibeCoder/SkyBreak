FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY init_db.py .
COPY skybreak/ ./skybreak/
COPY frontend/ ./frontend/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && python init_db.py
RUN cd frontend && npm install && npm run build || echo "React build attempted"
RUN mkdir -p /app/static && cp -r frontend/build/static/* /app/static/ || echo "No build output copied"
COPY . .
EXPOSE 8000
CMD ["python", "-m", "flask", "--app", "skybreak/app", "run", "--host=0.0.0.0", "--port=8000"]

COPY frontend/build/index.html /app/frontend/index.html || true
