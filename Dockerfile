# Multi-stage Docker build for PixelForge

# Stage 1: Backend builder
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements-basic.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-basic.txt

# Copy backend source
COPY backend/src/ ./src/
COPY backend/main.py .
COPY backend/pyproject.toml .


# Stage 2: Frontend builder
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build


# Stage 3: Final production image
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    libwebp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/

# Copy backend source
COPY backend/src/ ./src/
COPY backend/main.py .
COPY backend/pyproject.toml .

# Copy built frontend
COPY --from=frontend-builder /app/.next/standalone/ ./
COPY --from=frontend-builder /app/.next/static/ ./.next/static/
COPY --from=frontend-builder /app/public/ ./public/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create data directory
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DEBUG=false
ENV MAX_UPLOAD_SIZE=104857600  # 100MB
ENV DATA_DIR=/app/data

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Command to run both backend and frontend
CMD ["sh", "-c", "python main.py & nginx -g 'daemon off;'"]