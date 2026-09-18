"""FPL Charity Care Engine - Initial Schema Migration

Migration ID: 001
Created: 2024-01-17
Purpose: Create initial database schema for charity care eligibility engine

This migration establishes the core tables:
- hospitals: Participating hospital information
- federal_poverty_guidelines: Annual FPL data from HHS
- hospital_fap_thresholds: Hospital-specific assistance policies
- families: Applicant household and income data
- eligibility_assessments: Audit trail of all calculations

Includes indexes for query performance and referential integrity.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the initial schema migration."""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create hospitals table
    op.create_table(
        'hospitals',
        sa.Column('hospital_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('system_name', sa.String(255)),
        sa.Column('address_line1', sa.String(255), nullable=False),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.CHAR(2), nullable=False),
        sa.Column('zip_code', sa.String(10), nullable=False),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('fap_policy_url', sa.TEXT()),
        sa.Column('fap_notes', sa.TEXT()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('hospital_id')
    )
    
    # Create federal_poverty_guidelines table
    op.create_table(
        'federal_poverty_guidelines',
        sa.Column('guideline_id', sa.UUID(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('household_size', sa.Integer(), nullable=False),
        sa.Column('poverty_guideline', sa.Numeric(12, 2), nullable=False),
        sa.Column('source_url', sa.TEXT()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('guideline_id'),
        sa.UniqueConstraint('year', 'household_size'),
        sa.CheckConstraint('household_size >= 1', name='chk_fpg_household_size'),
        sa.CheckConstraint('poverty_guideline >= 0', name='chk_fpg_poverty_guideline')
    )
    
    # Create index on year and household_size for fast lookups
    op.create_index(
        'idx_fpg_year_size',
        'federal_poverty_guidelines',
        ['year', 'household_size']
    )
    
    # Create hospital_fap_thresholds table
    op.create_table(
        'hospital_fap_thresholds',
        sa.Column('threshold_id', sa.UUID(), nullable=False),
        sa.Column('hospital_id', sa.UUID(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('household_size', sa.Integer(), nullable=False),
        sa.Column('fpl_percentage', sa.Numeric(6, 2), nullable=False),
        sa.Column('coverage_type', sa.String(50), default='full_charity'),
        sa.Column('notes', sa.TEXT()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('threshold_id'),
        sa.UniqueConstraint('hospital_id', 'year', 'household_size', 'fpl_percentage'),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.hospital_id'], ondelete='CASCADE'),
        sa.CheckConstraint('household_size >= 1', name='chk_hft_household_size'),
        sa.CheckConstraint('fpl_percentage >= 0 AND fpl_percentage <= 1000', name='chk_hft_fpl_percentage')
    )
    
    # Create index on hospital_id and year
    op.create_index(
        'idx_hft_hospital_year',
        'hospital_fap_thresholds',
        ['hospital_id', 'year']
    )
    
    # Create families table
    op.create_table(
        'families',
        sa.Column('family_id', sa.UUID(), nullable=False),
        sa.Column('household_size', sa.Integer(), nullable=False),
        sa.Column('annual_gross_income', sa.Numeric(12, 2), nullable=False),
        sa.Column('income_source', sa.String(100)),
        sa.Column('state', sa.CHAR(2), nullable=False),
        sa.Column('cost_of_living_adjustment_factor', sa.Numeric(5, 3), default=1.000),
        sa.Column('application_reference', sa.String(100), unique=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('family_id'),
        sa.CheckConstraint('household_size >= 1', name='chk_fam_household_size'),
        sa.CheckConstraint('annual_gross_income >= 0', name='chk_fam_annual_gross_income')
    )
    
    # Create eligibility_assessments table (audit trail)
    op.create_table(
        'eligibility_assessments',
        sa.Column('assessment_id', sa.UUID(), nullable=False),
        sa.Column('family_id', sa.UUID(), nullable=False),
        sa.Column('hospital_id', sa.UUID(), nullable=False),
        sa.Column('assessment_year', sa.Integer(), nullable=False),
        sa.Column('fpl_guideline', sa.Numeric(12, 2), nullable=False),
        sa.Column('fpl_percentage', sa.Numeric(8, 4), nullable=False),
        sa.Column('fap_threshold_applied', sa.Numeric(6, 2), nullable=False),
        sa.Column('is_eligible', sa.Boolean(), nullable=False),
        sa.Column('coverage_type', sa.String(50)),
        sa.Column('notes', sa.TEXT()),
        sa.Column('calculated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.Column('calculated_by', sa.String(255)),
        sa.PrimaryKeyConstraint('assessment_id'),
        sa.ForeignKeyConstraint(['family_id'], ['families.family_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.hospital_id'], ondelete='CASCADE')
    )
    
    # Create indexes for eligibility_assessments
    op.create_index(
        'idx_ea_family',
        'eligibility_assessments',
        ['family_id']
    )
    op.create_index(
        'idx_ea_hospital',
        'eligibility_assessments',
        ['hospital_id']
    )
    
    # Add table comments for documentation
    op.execute("COMMENT ON TABLE hospitals IS 'Stores participating hospital information for charity care programs'")
    op.execute("COMMENT ON TABLE federal_poverty_guidelines IS 'Annual Federal Poverty Guidelines published by HHS'")
    op.execute("COMMENT ON TABLE hospital_fap_thresholds IS 'Hospital-specific Financial Assistance Policy thresholds based on FPL percentages'")
    op.execute("COMMENT ON TABLE families IS 'Stores applicant household and income information'")
    op.execute("COMMENT ON TABLE eligibility_assessments IS 'Audit trail of all charity care eligibility calculations'")


def downgrade() -> None:
    """Rollback the initial schema migration."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('eligibility_assessments')
    op.drop_table('families')
    op.drop_table('hospital_fap_thresholds')
    op.drop_table('federal_poverty_guidelines')
    op.drop_table('hospitals')
    
    # Note: We don't drop uuid-ossp extension as it may be used by other tables
