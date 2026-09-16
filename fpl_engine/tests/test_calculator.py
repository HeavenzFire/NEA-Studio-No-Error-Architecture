"""
Unit Tests for FPL Calculator & Eligibility Engine

Comprehensive test suite covering edge cases, validation, and business logic.
Run with: pytest tests/test_calculator.py -v
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, '/workspace/fpl_engine')

from calculator import (
    calculate_fpl_percentage,
    get_adjusted_income,
    FamilyIncome,
    EligibilityResult,
    format_currency,
    generate_assessment_summary,
)


class TestCalculateFPLPercentage:
    """Tests for the FPL percentage calculation function."""
    
    def test_basic_calculation(self):
        """Test basic FPL percentage calculation."""
        result = calculate_fpl_percentage(
            annual_income=Decimal("35000.00"),
            fpl_guideline=Decimal("30000.00")
        )
        assert result == Decimal("116.6667")
    
    def test_exact_fpl(self):
        """Test when income equals FPL (100%)."""
        result = calculate_fpl_percentage(
            annual_income=Decimal("30000.00"),
            fpl_guideline=Decimal("30000.00")
        )
        assert result == Decimal("100.0000")
    
    def test_zero_income(self):
        """Test with zero income (0% FPL)."""
        result = calculate_fpl_percentage(
            annual_income=Decimal("0.00"),
            fpl_guideline=Decimal("30000.00")
        )
        assert result == Decimal("0.0000")
    
    def test_double_fpl(self):
        """Test when income is double the FPL (200%)."""
        result = calculate_fpl_percentage(
            annual_income=Decimal("60000.00"),
            fpl_guideline=Decimal("30000.00")
        )
        assert result == Decimal("200.0000")
    
    def test_invalid_fpl_guideline_zero(self):
        """Test that zero FPL guideline raises ValueError."""
        with pytest.raises(ValueError, match="FPL guideline must be greater than zero"):
            calculate_fpl_percentage(
                annual_income=Decimal("30000.00"),
                fpl_guideline=Decimal("0.00")
            )
    
    def test_invalid_fpl_guideline_negative(self):
        """Test that negative FPL guideline raises ValueError."""
        with pytest.raises(ValueError, match="FPL guideline must be greater than zero"):
            calculate_fpl_percentage(
                annual_income=Decimal("30000.00"),
                fpl_guideline=Decimal("-1000.00")
            )
    
    def test_custom_precision(self):
        """Test custom decimal precision."""
        result = calculate_fpl_percentage(
            annual_income=Decimal("35000.00"),
            fpl_guideline=Decimal("30000.00"),
            round_to=2
        )
        assert result == Decimal("116.67")
    
    def test_high_precision(self):
        """Test high precision calculation."""
        result = calculate_fpl_percentage(
            annual_income=Decimal("35123.45"),
            fpl_guideline=Decimal("30000.00"),
            round_to=6
        )
        assert result == Decimal("117.078167")


class TestGetAdjustedIncome:
    """Tests for the cost-of-living adjusted income calculation."""
    
    def test_no_adjustment(self):
        """Test with no COL adjustment (factor = 1.0)."""
        result = get_adjusted_income(
            annual_income=Decimal("50000.00"),
            col_adjustment_factor=Decimal("1.000")
        )
        assert result == Decimal("50000.00")
    
    def test_col_increase(self):
        """Test with COL increase (factor > 1.0)."""
        result = get_adjusted_income(
            annual_income=Decimal("50000.00"),
            col_adjustment_factor=Decimal("1.150")
        )
        assert result == Decimal("57500.00")
    
    def test_col_decrease(self):
        """Test with COL decrease (factor < 1.0)."""
        result = get_adjusted_income(
            annual_income=Decimal("50000.00"),
            col_adjustment_factor=Decimal("0.850")
        )
        assert result == Decimal("42500.00")
    
    def test_rounding_to_cents(self):
        """Test that result is rounded to cents."""
        result = get_adjusted_income(
            annual_income=Decimal("50000.333"),
            col_adjustment_factor=Decimal("1.000")
        )
        assert result == Decimal("50000.33")
    
    def test_zero_income(self):
        """Test with zero income."""
        result = get_adjusted_income(
            annual_income=Decimal("0.00"),
            col_adjustment_factor=Decimal("1.150")
        )
        assert result == Decimal("0.00")


class TestFamilyIncomeModel:
    """Tests for the FamilyIncome Pydantic model validation."""
    
    def test_valid_family(self):
        """Test valid family income data."""
        family = FamilyIncome(
            household_size=4,
            annual_gross_income=Decimal("75000.00"),
            state="CA"
        )
        assert family.household_size == 4
        assert family.annual_gross_income == Decimal("75000.00")
        assert family.state == "CA"
        assert family.cost_of_living_adjustment_factor == Decimal("1.000")
    
    def test_state_uppercase_conversion(self):
        """Test that state is converted to uppercase."""
        family = FamilyIncome(
            household_size=3,
            annual_gross_income=Decimal("45000.00"),
            state="ca"
        )
        assert family.state == "CA"
    
    def test_invalid_household_size_zero(self):
        """Test that zero household size raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FamilyIncome(
                household_size=0,
                annual_gross_income=Decimal("30000.00"),
                state="NY"
            )
    
    def test_invalid_household_size_negative(self):
        """Test that negative household size raises validation error."""
        with pytest.raises(Exception):
            FamilyIncome(
                household_size=-1,
                annual_gross_income=Decimal("30000.00"),
                state="NY"
            )
    
    def test_invalid_income_negative(self):
        """Test that negative income raises validation error."""
        with pytest.raises(Exception):
            FamilyIncome(
                household_size=2,
                annual_gross_income=Decimal("-5000.00"),
                state="TX"
            )
    
    def test_invalid_state_code_length(self):
        """Test that invalid state code length raises validation error."""
        with pytest.raises(Exception):
            FamilyIncome(
                household_size=1,
                annual_gross_income=Decimal("20000.00"),
                state="California"
            )
    
    def test_col_factor_out_of_range_high(self):
        """Test that COL factor > 2.0 raises validation error."""
        with pytest.raises(Exception):
            FamilyIncome(
                household_size=3,
                annual_gross_income=Decimal("40000.00"),
                state="FL",
                cost_of_living_adjustment_factor=Decimal("2.500")
            )
    
    def test_col_factor_out_of_range_low(self):
        """Test that COL factor < 0.5 raises validation error."""
        with pytest.raises(Exception):
            FamilyIncome(
                household_size=3,
                annual_gross_income=Decimal("40000.00"),
                state="FL",
                cost_of_living_adjustment_factor=Decimal("0.300")
            )
    
    def test_custom_col_factor(self):
        """Test custom COL adjustment factor."""
        family = FamilyIncome(
            household_size=2,
            annual_gross_income=Decimal("55000.00"),
            state="NY",
            cost_of_living_adjustment_factor=Decimal("1.250")
        )
        assert family.cost_of_living_adjustment_factor == Decimal("1.250")


class TestFormatCurrency:
    """Tests for currency formatting utility."""
    
    def test_standard_amount(self):
        """Test formatting standard amount."""
        result = format_currency(Decimal("1234.56"))
        assert result == "$1,234.56"
    
    def test_large_amount(self):
        """Test formatting large amount."""
        result = format_currency(Decimal("1234567.89"))
        assert result == "$1,234,567.89"
    
    def test_zero_amount(self):
        """Test formatting zero."""
        result = format_currency(Decimal("0.00"))
        assert result == "$0.00"
    
    def test_small_amount(self):
        """Test formatting small amount."""
        result = format_currency(Decimal("0.99"))
        assert result == "$0.99"


class TestGenerateAssessmentSummary:
    """Tests for assessment summary generation."""
    
    def test_eligible_summary(self):
        """Test summary generation for eligible applicant."""
        family = FamilyIncome(
            household_size=4,
            annual_gross_income=Decimal("45000.00"),
            state="IL"
        )
        
        result = EligibilityResult(
            is_eligible=True,
            fpl_percentage=Decimal("144.2308"),
            fpl_guideline=Decimal("31200.00"),
            fap_threshold_applied=Decimal("200.00"),
            coverage_type="full_charity",
            hospital_id="test-hospital-uuid",
            assessment_year=2024,
            notes="Qualifies for full charity care"
        )
        
        summary = generate_assessment_summary(result, family)
        
        assert "ELIGIBLE" in summary
        assert "Household Size: 4" in summary
        assert "$45,000.00" in summary
        assert "144.2308%" in summary
        assert "full_charity" in summary
    
    def test_not_eligible_summary(self):
        """Test summary generation for ineligible applicant."""
        family = FamilyIncome(
            household_size=2,
            annual_gross_income=Decimal("85000.00"),
            state="CA"
        )
        
        result = EligibilityResult(
            is_eligible=False,
            fpl_percentage=Decimal("416.6667"),
            fpl_guideline=Decimal("20440.00"),
            fap_threshold_applied=Decimal("200.00"),
            coverage_type="none",
            hospital_id="test-hospital-uuid",
            assessment_year=2024,
            notes="Income exceeds all available FAP thresholds."
        )
        
        summary = generate_assessment_summary(result, family)
        
        assert "NOT ELIGIBLE" in summary
        assert "Income exceeds all available FAP thresholds" in summary


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_very_large_household(self):
        """Test with very large household size."""
        family = FamilyIncome(
            household_size=15,
            annual_gross_income=Decimal("100000.00"),
            state="TX"
        )
        assert family.household_size == 15
    
    def test_very_high_income(self):
        """Test with very high income."""
        family = FamilyIncome(
            household_size=3,
            annual_gross_income=Decimal("5000000.00"),
            state="NY"
        )
        assert family.annual_gross_income == Decimal("5000000.00")
    
    def test_minimum_income(self):
        """Test with minimum positive income."""
        family = FamilyIncome(
            household_size=1,
            annual_gross_income=Decimal("0.01"),
            state="AL"
        )
        assert family.annual_gross_income == Decimal("0.01")
    
    def test_single_person_household(self):
        """Test with single person household."""
        family = FamilyIncome(
            household_size=1,
            annual_gross_income=Decimal("15000.00"),
            state="VT"
        )
        assert family.household_size == 1


# Run with: pytest tests/test_calculator.py -v
# Or: python -m pytest tests/test_calculator.py -v

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
