FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgdal-dev \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libxcb1 \
        libx11-xcb1 \
        libxrender1 \
        libxext6 \
        libsm6 \
        libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir opencv-python-headless
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/yolov8n.pt /srv/yolov8n.pt
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/app ./app
COPY scripts ./scripts
COPY ml ./ml
COPY spatial ./spatial
COPY analytics ./analytics
COPY alerts ./alerts
COPY configs ./configs

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

