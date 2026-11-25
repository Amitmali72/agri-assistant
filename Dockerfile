FROM python:3.10-slim AS backend-base

WORKDIR /app

# Install system dependencies for audio (ffmpeg) and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /web
COPY frontend-web/package*.json ./
RUN npm install
COPY frontend-web/ .
RUN npm run build

# Final Runtime Image
FROM backend-base
WORKDIR /app
COPY . .
COPY --from=frontend-build /web/dist /app/frontend-web/dist

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
