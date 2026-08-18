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

# Pre-install CPU torch to satisfy dependencies and avoid massive 3GB CUDA downloads
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install API dependencies (shared models)
COPY apps/api/requirements.txt ./api-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt

# Install other ML dependencies
RUN pip install --no-cache-dir "numpy<2.0.0" ultralytics opencv-python-headless scipy scikit-learn
RUN pip install --no-cache-dir PytorchWildlife

# Copy code
COPY apps/api/yolov8n.pt /srv/yolov8n.pt
COPY apps/api/app ./app
COPY workers ./workers
COPY ml ./ml
COPY spatial ./spatial
COPY analytics ./analytics
COPY alerts ./alerts
COPY configs ./configs

CMD ["celery", "-A", "workers.celery_app:celery_app", "worker", "--loglevel=INFO", "--concurrency=2"]
