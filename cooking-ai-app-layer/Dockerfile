# Build context must contain BOTH folders side by side:
#   .
#   ├── cooking-ai-app-layer/   (this Dockerfile lives here)
#   └── cooking-ai-data-layer/  (the package from the previous step)
#
# Build from the parent directory:
#   docker build -f cooking-ai-app-layer/Dockerfile -t cooking-ai-app .

FROM python:3.11-slim

WORKDIR /srv

# 1. Install the Data/Model Layer as its own package first
COPY cooking-ai-data-layer /data_layer
RUN pip install --no-cache-dir -e /data_layer

# 2. Install the Application Layer's own dependencies
COPY cooking-ai-app-layer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the application code
COPY cooking-ai-app-layer/ .

ENV PORT=5000
EXPOSE 5000

# --preload loads the data/model layer ONCE in the master process before
# forking workers, instead of once per worker — important here since model
# loading is the expensive part. --timeout is generous because the very
# first request after a cold start may trigger a one-time model download.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--preload", "--timeout", "120", "run:app"]
