# The Loom - Production Dockerfile
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Security: Run as non-root user
RUN groupadd -r loom && useradd -r -g loom loom

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=loom:loom core/ ./core/
COPY --chown=loom:loom ui/ ./ui/
COPY --chown=loom:loom agents/ ./agents/
COPY --chown=loom:loom models/ ./models/
COPY --chown=loom:loom tests/ ./tests/
COPY --chown=loom:loom pyproject.toml .
COPY --chown=loom:loom requirements.txt .

# Create data directories
RUN mkdir -p /app/data /app/.loom /app/generated_images /app/chroma_db && \
    chown -R loom:loom /app

# Switch to non-root user
USER loom

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOOM_DATA_DIR=/app/data
ENV LOOM_GRAPH_DB=/app/.loom/graph.db
ENV LOOM_EVENTS_DB=/app/.loom/events.db

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/ops/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "ui.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
