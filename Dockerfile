FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY init_db.py .
COPY skybreak/ ./skybreak/
RUN pip install --no-cache-dir pytest && python -c "from skybreak.airport import init_db; init_db()"
COPY . .
EXPOSE 8000
CMD ["python", "-m", "pytest"]
