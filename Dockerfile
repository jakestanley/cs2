FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app_config.py registry.py portal_server.py ./
COPY web ./web

CMD ["python3", "portal_server.py"]
