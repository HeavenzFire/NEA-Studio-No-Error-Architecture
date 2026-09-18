# Sovereign Core Shield - Production Docker Image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and compilation
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY fpl_engine/ ./fpl_engine/
COPY scripts/ ./scripts/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    LOG_LEVEL=INFO

# Expose API port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "\
import asyncio; \
import os; \
from sqlalchemy.ext.asyncio import create_async_engine; \
async def check(): \
    try: \
        engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql://test:test@localhost/test')); \
        async with engine.connect() as conn: pass; \
        return 0; \
    except: return 1; \
exit(asyncio.run(check()))" || exit 1

# Run migrations and start API server
CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn fpl_engine.api:app --host 0.0.0.0 --port 8000"]
