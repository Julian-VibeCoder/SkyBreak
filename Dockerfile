FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev nodejs npm && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY init_db.py .
COPY skybreak/ ./skybreak/
COPY frontend/ ./frontend/
RUN pip install --no-cache-dir flask pytest && python init_db.py
RUN cd frontend && npm install && npm run build || echo "React build attempted"
COPY . .
EXPOSE 8000
CMD ["python", "-m", "flask", "--app", "skybreak/app", "run", "--host=0.0.0.0", "--port=8000"]
