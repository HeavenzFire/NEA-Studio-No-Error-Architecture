# Sovereign Core Shield - Deployment & Operations Guide

## 🏛️ System Overview

**Sovereign Core Shield** is an enterprise-hardened financial assistance eligibility engine designed for hospital charity care programs. It provides:

- **Sliding-scale eligibility calculations** based on Federal Poverty Level (FPL) guidelines
- **Hospital-specific Financial Assistance Policy (FAP)** enforcement
- **Audit-ready compliance** with immutable lifecycle logging
- **Production-grade APIs** with RFC 7807 error models
- **Automated deployment pipelines** for reproducible rollouts

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Database Migrations](#database-migrations)
4. [Data Seeding](#data-seeding)
5. [API Reference](#api-reference)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Docker Deployment](#docker-deployment)
8. [Compliance & Auditing](#compliance--auditing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python**: 3.11+ 
- **PostgreSQL**: 15+ with `uuid-ossp` extension
- **Docker**: 24+ (for containerized deployment)
- **Alembic**: 1.12+ (for database migrations)

### Environment Variables

Create a `.env` file or export these variables:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/fpl_charity_care

# Application Settings
APP_ENV=production  # development, staging, production
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR
CURRENT_USER=system # For audit logging

# Optional: Cost-of-Living Adjustment
COL_ADJUSTMENT_ENABLED=false
DEFAULT_COL_FACTOR=1.000
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt** should include:
```
sqlalchemy>=2.0.0
asyncpg>=0.29.0
pydantic>=2.0.0
alembic>=1.12.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### 2. Create Database

```bash
createdb fpl_charity_care
psql -d fpl_charity_care -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### 3. Run Migrations

```bash
alembic upgrade head
```

### 4. Seed Reference Data

```bash
# Load federal poverty guidelines and sample hospitals
python scripts/seed_data.py

# Load Texas hospital FAP data (optional)
export DATABASE_URL="postgresql+asyncpg://..."
python scripts/seed_texas_hospitals.py
```

### 5. Run Tests

```bash
pytest fpl_engine/tests/ -v
```

---

## Database Migrations

### Alembic Configuration

Migrations are managed via Alembic. Configuration files:

- `alembic.ini` - Migration settings
- `migrations/env.py` - Execution environment
- `migrations/versions/` - Individual migration scripts

### Available Migrations

| Revision | Description | Date |
|----------|-------------|------|
| `001` | Initial schema (tables, indexes, constraints) | 2024-01-17 |
| `002` | Lifecycle triggers (audit logging, validation) | 2024-01-17 |

### Common Commands

```bash
# Check current migration status
alembic current

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Generate new migration (autogenerate from models)
alembic revision --autogenerate -m "description"

# Apply all migrations in transaction
alembic upgrade head --sql
```

### Migration Best Practices

1. **Always test migrations on staging** before production
2. **Include downgrade functions** for every migration
3. **Use transactional migrations** (`transaction_per_migration=True`)
4. **Document breaking changes** in migration docstrings
5. **Never modify existing migrations** - create new ones instead

---

## Data Seeding

### Federal Poverty Guidelines

The `seed_data.py` script loads annual FPL data from HHS:

```python
# 2024 FPL Guidelines (48 contiguous states)
Household Size 1: $15,060
Household Size 2: $20,440
Household Size 3: $25,820
Household Size 4: $31,200
# +$5,380 for each additional person
```

### Hospital FAP Policies

Two seeding scripts available:

1. **`scripts/seed_data.py`** - Sample hospitals (generic)
2. **`scripts/seed_texas_hospitals.py`** - Real Texas hospital data

#### Texas Hospital Systems Included

| Hospital System | Locations | FPL Multipliers |
|----------------|-----------|-----------------|
| UT Health East Texas | Tyler | 200%, 400% |
| CHRISTUS Health | Tyler, Grand Prairie | 200%, 400% |
| Baylor Scott & White | Dallas, Fort Worth | 200%, 300%, 400% |

### Running Seed Scripts

```bash
# Interactive mode (prompts for confirmation)
python scripts/seed_texas_hospitals.py

# Non-interactive mode
echo "yes" | python scripts/seed_texas_hospitals.py

# With custom database URL
DATABASE_URL="postgresql+asyncpg://..." python scripts/seed_texas_hospitals.py
```

### Verification

After seeding, verify data integrity:

```sql
-- Count Texas hospitals
SELECT COUNT(*) FROM hospitals WHERE state = 'TX';

-- View FAP thresholds for specific hospital
SELECT h.name, hft.year, hft.household_size, 
       hft.fpl_percentage, hft.coverage_type
FROM hospital_fap_thresholds hft
JOIN hospitals h ON hft.hospital_id = h.hospital_id
WHERE h.name LIKE '%Baylor%'
ORDER BY hft.household_size, hft.fpl_percentage;
```

---

## API Reference

### Eligibility Assessment Endpoint

**POST** `/api/v1/eligibility/assess`

Evaluate patient eligibility for hospital charity care.

#### Request Body

```json
{
  "household_size": 3,
  "annual_gross_income": 52000.00,
  "state": "TX",
  "cost_of_living_adjustment_factor": 1.000,
  "hospital_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "assessment_year": 2024
}
```

#### Response (200 OK)

```json
{
  "is_eligible": true,
  "fpl_percentage": 201.0385,
  "fpl_guideline": 25820.00,
  "fap_threshold_applied": 300.00,
  "coverage_type": "discounted",
  "hospital_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "assessment_year": 2024,
  "notes": "50% discount for patients 200%-300% FPL."
}
```

#### Error Responses (RFC 7807)

**400 Bad Request**
```json
{
  "type": "https://api.sovereignshield.dev/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid household size: must be >= 1",
  "instance": "/api/v1/eligibility/assess"
}
```

**404 Not Found**
```json
{
  "type": "https://api.sovereignshield.dev/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "No FPL guideline found for year 2024 and household size 15",
  "instance": "/api/v1/eligibility/assess"
}
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci-cd-pipeline.yml` defines automated testing and deployment:

#### Jobs

1. **test** - Unit tests + integration tests
   - Linting (black, flake8)
   - Pytest with coverage
   - Codecov upload

2. **health-check** - Database + schema verification
   - PostgreSQL connectivity
   - Table existence checks
   - Migration status

3. **build-docker** - Container image (main branch only)
   - Multi-architecture build
   - Push to GHCR

4. **deploy-staging** - Staging deployment (main branch only)
   - Kubernetes manifest update
   - Migration execution
   - Rollback monitoring

### Trigger Conditions

| Event | Branches | Jobs Executed |
|-------|----------|---------------|
| Push | `main`, `develop` | test, health-check |
| Pull Request | `main` | test, health-check |
| Merge to `main` | `main` | All jobs + deploy |

### Adding Environments

Configure GitHub environments for deployment targets:

1. Go to **Settings → Environments**
2. Add `staging` and `production`
3. Configure required reviewers (for production)
4. Set environment-specific secrets

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY fpl_engine/ ./fpl_engine/
COPY scripts/ ./scripts/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; import os; \
    asyncio.run(create_async_engine(os.getenv('DATABASE_URL')).connect())"

CMD ["alembic", "upgrade", "head", "&&", "python", "-m", "uvicorn", "fpl_engine.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/fpl_charity_care
      APP_ENV: production
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: fpl_charity_care
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Running with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Run migrations manually
docker-compose exec api alembic upgrade head

# Seed data
docker-compose exec api python scripts/seed_texas_hospitals.py
```

---

## Compliance & Auditing

### Audit Trail Features

1. **Immutable Assessment Logs**
   - Every eligibility calculation recorded in `eligibility_assessments`
   - Includes family_id, hospital_id, FPL percentage, result

2. **FAP Threshold Change Tracking**
   - All INSERT/UPDATE/DELETE operations logged to `fap_threshold_audit_log`
   - Captures old and new values
   - Timestamped with `changed_at` and `changed_by`

3. **Lifecycle Triggers**
   - Automatic `updated_at` timestamp management
   - FAP consistency validation (full charity must be lowest threshold)
   - Deferred constraint checking for bulk operations

### Audit Queries

```sql
-- View all changes to a hospital's FAP policy
SELECT 
    h.name AS hospital_name,
    fal.change_type,
    fal.old_fpl_percentage,
    fal.new_fpl_percentage,
    fal.old_coverage_type,
    fal.new_coverage_type,
    fal.changed_at,
    fal.changed_by
FROM fap_threshold_audit_log fal
JOIN hospitals h ON fal.hospital_id = h.hospital_id
WHERE h.name = 'Baylor Scott & White Medical Center - Dallas'
ORDER BY fal.changed_at DESC;

-- Retrieve assessment history for a family
SELECT 
    h.name AS hospital_name,
    ea.assessment_year,
    ea.fpl_percentage,
    ea.is_eligible,
    ea.coverage_type,
    ea.calculated_at
FROM eligibility_assessments ea
JOIN hospitals h ON ea.hospital_id = h.hospital_id
WHERE ea.family_id = 'xxx-xxx-xxx'
ORDER BY ea.calculated_at DESC;
```

### Compliance Reports

Generate monthly compliance reports:

```bash
python scripts/generate_compliance_report.py \
  --year 2024 \
  --month 1 \
  --format pdf \
  --output /reports/january_2024_compliance.pdf
```

---

## Troubleshooting

### Common Issues

#### Migration Failures

**Error**: `Migration script 'xxx' was not found`

**Solution**:
```bash
# Ensure migrations directory is in Python path
export PYTHONPATH=/path/to/workspace:$PYTHONPATH
alembic upgrade head
```

#### Database Connection Errors

**Error**: `could not translate host name "localhost" to address`

**Solution**:
```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:5432/dbname
```

#### FAP Threshold Validation Errors

**Error**: `Full charity threshold must be at the lowest FPL percentage`

**Cause**: Attempting to insert a `full_charity` threshold at a higher FPL % than existing `discounted` thresholds.

**Solution**: Insert thresholds in order (lowest FPL % first) or use deferred transactions:
```sql
BEGIN;
SET CONSTRAINTS trg_fap_validate_consistency DEFERRED;
-- Insert all thresholds
COMMIT;
```

### Logging

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export DATABASE_ECHO=true  # SQLAlchemy query logging
```

View structured logs:

```bash
journalctl -u sovereign-shield-api -f
# Or with Docker:
docker-compose logs -f api
```

---

## Support & Contact

- **Documentation**: `/workspace/README.md`
- **Issue Tracker**: GitHub Issues
- **Emergency Contact**: [Your contact information]

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-17  
**Maintained By**: Sovereign Core Shield Engineering Team
