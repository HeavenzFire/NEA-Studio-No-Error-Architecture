# FPL Charity Care Engine

Production-ready Federal Poverty Level (FPL) calculator and hospital charity care eligibility engine.

## Overview

This engine provides:
- **FPL Percentage Calculation**: Accurate computation of income as a percentage of Federal Poverty Guidelines
- **Cost-of-Living Adjustments**: Optional COL factors for regional adjustments
- **Hospital-Specific FAP Thresholds**: Support for multiple hospital Financial Assistance Policies
- **Eligibility Assessment**: Automated determination of charity care eligibility
- **Audit Trail**: Complete logging of all assessments for compliance

## Directory Structure

```
fpl_engine/
├── __init__.py              # Package initialization
├── calculator.py            # Core calculation and eligibility logic
├── schema.sql               # PostgreSQL database schema
├── tests/
│   ├── __init__.py
│   └── test_calculator.py   # Unit tests
└── README.md                # This file

scripts/
└── seed_data.py             # Database seeding script
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Required packages: `pydantic`, `sqlalchemy`, `asyncpg`

```bash
pip install pydantic sqlalchemy asyncpg
```

## Database Setup

### 1. Create the database schema

```bash
psql -U username -d fpl_charity_care -f fpl_engine/schema.sql
```

### 2. Seed reference data

Update the database connection string in `scripts/seed_data.py`:

```python
DATABASE_URL = "postgresql+asyncpg://username:password@localhost:5432/fpl_charity_care"
```

Then run:

```bash
python scripts/seed_data.py
```

This will populate:
- 2024 Federal Poverty Guidelines (household sizes 1-10)
- Sample hospitals with FAP thresholds

## Usage

### Basic FPL Calculation

```python
from decimal import Decimal
from fpl_engine.calculator import calculate_fpl_percentage, get_adjusted_income

# Calculate FPL percentage
fpl_pct = calculate_fpl_percentage(
    annual_income=Decimal("35000.00"),
    fpl_guideline=Decimal("30000.00")
)
print(f"FPL Percentage: {fpl_pct}%")  # Output: 116.6667%

# Apply cost-of-living adjustment
adjusted = get_adjusted_income(
    annual_income=Decimal("50000.00"),
    col_adjustment_factor=Decimal("1.150")
)
print(f"Adjusted Income: ${adjusted}")  # Output: $57,500.00
```

### Eligibility Assessment

```python
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fpl_engine.calculator import FamilyIncome, evaluate_hospital_assistance

async def check_eligibility():
    # Define family
    family = FamilyIncome(
        household_size=4,
        annual_gross_income=Decimal("75000.00"),
        state="CA",
        cost_of_living_adjustment_factor=Decimal("1.150")
    )
    
    # Connect to database
    engine = create_async_engine(DATABASE_URL)
    
    async with AsyncSession(engine) as session:
        result = await evaluate_hospital_assistance(
            session=session,
            family=family,
            hospital_id="your-hospital-uuid-here"
        )
        
        print(f"Eligible: {result.is_eligible}")
        print(f"FPL %: {result.fpl_percentage}%")
        print(f"Coverage: {result.coverage_type}")

asyncio.run(check_eligibility())
```

### Generate Assessment Summary

```python
from fpl_engine.calculator import generate_assessment_summary

summary = generate_assessment_summary(result, family)
print(summary)
```

Output:
```
═══════════════════════════════════════════════════
CHARITY CARE ELIGIBILITY ASSESSMENT
═══════════════════════════════════════════════════

Status: ELIGIBLE

Household Information:
  - Household Size: 4 person(s)
  - State: CA
  - Annual Gross Income: $75,000.00
  - COL Adjustment Factor: 1.150x
  - Adjusted Income: $86,250.00

FPL Analysis:
  - Assessment Year: 2024
  - FPL Guideline: $31,200.00
  - FPL Percentage: 276.4423%

Hospital Policy:
  - Hospital ID: uuid-here
  - Threshold Applied: 300.00% of FPL
  - Coverage Type: discounted

Notes: Sliding scale discount 200-300% FPL
═══════════════════════════════════════════════════
```

## Data Models

### FamilyIncome

```python
class FamilyIncome(BaseModel):
    household_size: int                    # Must be >= 1
    annual_gross_income: Decimal           # Must be >= 0
    state: str                             # 2-letter code, auto-uppercased
    cost_of_living_adjustment_factor: Decimal  # 0.5 - 2.0, default 1.0
```

### EligibilityResult

```python
class EligibilityResult(BaseModel):
    is_eligible: bool
    fpl_percentage: Decimal
    fpl_guideline: Decimal
    fap_threshold_applied: Decimal
    coverage_type: str
    hospital_id: str
    assessment_year: int
    notes: Optional[str]
```

## Testing

Run the unit tests:

```bash
cd /workspace
python -c "from fpl_engine.tests.test_calculator import *; import pytest; pytest.main(['-v', 'fpl_engine/tests/test_calculator.py'])"
```

Or run functional tests directly:

```bash
python << 'EOF'
from fpl_engine.calculator import *
from decimal import Decimal

# Run your own test scenarios here
result = calculate_fpl_percentage(Decimal("35000.00"), Decimal("30000.00"))
print(f"Test: {result == Decimal('116.6667')}")
EOF
```

## Federal Poverty Guidelines Reference

For 2024 (48 contiguous states + DC):

| Household Size | FPL Guideline |
|---------------|---------------|
| 1             | $15,060       |
| 2             | $20,440       |
| 3             | $25,820       |
| 4             | $31,200       |
| 5             | $36,580       |
| 6             | $41,960       |
| 7             | $47,340       |
| 8             | $52,720       |

Add $5,380 for each additional person beyond 8.

Source: [HHS Poverty Guidelines](https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines)

## Hospital FAP Thresholds

Each hospital can define multiple FAP thresholds per household size:

- **full_charity**: 100% charity care (typically up to 200-250% FPL)
- **discounted**: Sliding scale discounts (typically 200-400% FPL)
- **partial_discount**: Limited assistance (typically 300-500% FPL)

The engine automatically selects the most generous threshold the applicant qualifies for.

## Error Handling

The engine raises `ValueError` when:
- FPL guideline not found for the specified year/household size
- No FAP thresholds exist for the hospital/year/household size
- Invalid FPL guideline (zero or negative)

Validation errors from Pydantic are raised when:
- Household size < 1
- Income < 0
- State code not 2 characters
- COL factor outside 0.5-2.0 range

## Next Steps

1. **Update FPL Guidelines Annually**: Run the seed script each year with new HHS data
2. **Add Real Hospital Data**: Replace sample hospitals with actual FAP policies
3. **Integrate with Application Layer**: Connect to your intake forms
4. **Add PHI Handling**: Implement proper HIPAA-compliant data storage for patient information
5. **Deploy**: Use Docker/Terraform for production deployment (Option B)

## License

Production-ready draft for immediate use.
