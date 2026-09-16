"""
FPL Calculator & Eligibility Engine

Production-ready module for Federal Poverty Level calculations and hospital charity care eligibility assessment.
Uses SQLAlchemy for database interaction and Pydantic for data validation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


# --- Data Models ---

class FamilyIncome(BaseModel):
    """Represents family income and household information."""
    household_size: int = Field(gt=0, description="Number of people in the household")
    annual_gross_income: Decimal = Field(ge=0, description="Annual gross income in USD")
    state: str = Field(min_length=2, max_length=2, description="Two-letter state code")
    cost_of_living_adjustment_factor: Decimal = Field(
        default=Decimal("1.000"), 
        ge=Decimal("0.500"), 
        le=Decimal("2.000"),
        description="Cost of living adjustment multiplier"
    )

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        return v.upper()


class EligibilityResult(BaseModel):
    """Represents the result of a charity care eligibility assessment."""
    is_eligible: bool
    fpl_percentage: Decimal
    fpl_guideline: Decimal
    fap_threshold_applied: Decimal
    coverage_type: str
    hospital_id: str
    assessment_year: int
    notes: Optional[str] = None


# --- FPL Calculator Functions ---

def calculate_fpl_percentage(
    annual_income: Decimal,
    fpl_guideline: Decimal,
    round_to: int = 4
) -> Decimal:
    """
    Calculate the percentage of Federal Poverty Level.
    
    Formula: (Annual Income / FPL Guideline) * 100
    
    Args:
        annual_income: Total annual gross income
        fpl_guideline: Federal poverty guideline for household size and year
        round_to: Decimal precision for the result
    
    Returns:
        FPL percentage as a Decimal
    
    Raises:
        ValueError: If FPL guideline is zero or negative
    """
    if fpl_guideline <= 0:
        raise ValueError("FPL guideline must be greater than zero.")
    
    percentage = (annual_income / fpl_guideline) * Decimal("100.0")
    quantizer = Decimal("1." + "0" * round_to)
    return percentage.quantize(quantizer, rounding=ROUND_HALF_UP)


def get_adjusted_income(
    annual_income: Decimal,
    col_adjustment_factor: Decimal
) -> Decimal:
    """
    Apply cost-of-living adjustment to income if applicable.
    
    Args:
        annual_income: Original annual income
        col_adjustment_factor: COL adjustment multiplier
    
    Returns:
        Adjusted income for evaluation (rounded to cents)
    """
    adjusted = annual_income * col_adjustment_factor
    return adjusted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# --- Database Interaction Functions ---

async def get_fpl_guideline(
    session: AsyncSession,
    year: int,
    household_size: int
) -> Optional[Decimal]:
    """
    Fetch the FPL guideline for a given year and household size.
    
    Args:
        session: Active database session
        year: Assessment year
        household_size: Number of people in household
    
    Returns:
        FPL guideline as Decimal, or None if not found
    """
    query = text("""
        SELECT poverty_guideline 
        FROM federal_poverty_guidelines 
        WHERE year = :year AND household_size = :household_size
    """)
    
    result = await session.execute(query, {"year": year, "household_size": household_size})
    guideline = result.scalar_one_or_none()
    
    return Decimal(str(guideline)) if guideline is not None else None


async def get_hospital_fap_thresholds(
    session: AsyncSession,
    hospital_id: str,
    year: int,
    household_size: int
) -> List[dict]:
    """
    Fetch all applicable FAP thresholds for a hospital, year, and household size.
    
    Args:
        session: Active database session
        hospital_id: UUID of the hospital
        year: Assessment year
        household_size: Number of people in household
    
    Returns:
        List of threshold dictionaries with fpl_percentage, coverage_type, and notes
    """
    query = text("""
        SELECT fpl_percentage, coverage_type, notes
        FROM hospital_fap_thresholds
        WHERE hospital_id = :hospital_id
          AND year = :year
          AND household_size = :household_size
        ORDER BY fpl_percentage DESC
    """)
    
    result = await session.execute(
        query, 
        {
            "hospital_id": hospital_id, 
            "year": year, 
            "household_size": household_size
        }
    )
    
    rows = result.mappings().all()
    return [dict(row) for row in rows]


# --- Eligibility Evaluation ---

async def evaluate_hospital_assistance(
    session: AsyncSession,
    family: FamilyIncome,
    hospital_id: str,
    assessment_year: Optional[int] = None
) -> EligibilityResult:
    """
    Evaluate a family's eligibility for hospital charity care.
    
    Args:
        session: Active database session
        family: Family income and household details
        hospital_id: UUID of the hospital
        assessment_year: Year to evaluate against (defaults to current year)
    
    Returns:
        EligibilityResult with full assessment details
    
    Raises:
        ValueError: If FPL guideline or FAP thresholds are not found
    """
    if assessment_year is None:
        assessment_year = datetime.utcnow().year
    
    # Get FPL guideline
    fpl_guideline = await get_fpl_guideline(session, assessment_year, family.household_size)
    if fpl_guideline is None:
        raise ValueError(
            f"No FPL guideline found for year {assessment_year} and household size {family.household_size}"
        )
    
    # Apply COL adjustment
    adjusted_income = get_adjusted_income(
        family.annual_gross_income,
        family.cost_of_living_adjustment_factor
    )
    
    # Calculate FPL percentage
    fpl_percentage = calculate_fpl_percentage(adjusted_income, fpl_guideline)
    
    # Get hospital-specific thresholds
    thresholds = await get_hospital_fap_thresholds(
        session,
        hospital_id,
        assessment_year,
        family.household_size
    )
    
    if not thresholds:
        raise ValueError(
            f"No FAP thresholds found for hospital {hospital_id} in {assessment_year} for household size {family.household_size}"
        )
    
    # Find the best matching threshold (highest threshold the family qualifies for)
    eligible_threshold = None
    for threshold in thresholds:
        threshold_pct = Decimal(str(threshold["fpl_percentage"]))
        if fpl_percentage <= threshold_pct:
            eligible_threshold = threshold
            break  # Since sorted desc, first match is the most generous
    
    is_eligible = eligible_threshold is not None
    
    if not is_eligible:
        return EligibilityResult(
            is_eligible=False,
            fpl_percentage=fpl_percentage,
            fpl_guideline=fpl_guideline,
            fap_threshold_applied=Decimal(str(thresholds[-1]["fpl_percentage"])),
            coverage_type="none",
            hospital_id=hospital_id,
            assessment_year=assessment_year,
            notes="Income exceeds all available FAP thresholds."
        )
    
    return EligibilityResult(
        is_eligible=True,
        fpl_percentage=fpl_percentage,
        fpl_guideline=fpl_guideline,
        fap_threshold_applied=Decimal(str(eligible_threshold["fpl_percentage"])),
        coverage_type=eligible_threshold["coverage_type"],
        hospital_id=hospital_id,
        assessment_year=assessment_year,
        notes=eligible_threshold.get("notes")
    )


# --- Utility Functions ---

def format_currency(amount: Decimal) -> str:
    """Format Decimal as USD currency string."""
    return f"${amount:,.2f}"


def generate_assessment_summary(result: EligibilityResult, family: FamilyIncome) -> str:
    """
    Generate a human-readable summary of the eligibility assessment.
    
    Args:
        result: EligibilityResult from evaluation
        family: Original FamilyIncome data
    
    Returns:
        Formatted summary string
    """
    status = "ELIGIBLE" if result.is_eligible else "NOT ELIGIBLE"
    summary = f"""
    ═══════════════════════════════════════════════════
    CHARITY CARE ELIGIBILITY ASSESSMENT
    ═══════════════════════════════════════════════════
    
    Status: {status}
    
    Household Information:
      - Household Size: {family.household_size} person(s)
      - State: {family.state}
      - Annual Gross Income: {format_currency(family.annual_gross_income)}
      - COL Adjustment Factor: {family.cost_of_living_adjustment_factor}x
      - Adjusted Income: {format_currency(get_adjusted_income(family.annual_gross_income, family.cost_of_living_adjustment_factor))}
    
    FPL Analysis:
      - Assessment Year: {result.assessment_year}
      - FPL Guideline: {format_currency(result.fpl_guideline)}
      - FPL Percentage: {result.fpl_percentage}%
    
    Hospital Policy:
      - Hospital ID: {result.hospital_id}
      - Threshold Applied: {result.fap_threshold_applied}% of FPL
      - Coverage Type: {result.coverage_type}
    
    Notes: {result.notes or 'None'}
    ═══════════════════════════════════════════════════
    """
    return summary.strip()
