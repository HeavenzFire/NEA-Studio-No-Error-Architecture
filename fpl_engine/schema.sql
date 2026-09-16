-- FPL Charity Care Engine Database Schema
-- PostgreSQL schema for Federal Poverty Level calculations and hospital assistance eligibility

-- Enable UUID extension if not already present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Hospitals table: Stores participating hospital information
CREATE TABLE hospitals (
    hospital_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    system_name VARCHAR(255),
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    phone_number VARCHAR(20),
    fap_policy_url TEXT,
    fap_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Federal Poverty Guidelines (FPL) table: Updated annually by HHS
CREATE TABLE federal_poverty_guidelines (
    guideline_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INT NOT NULL,
    household_size INT NOT NULL CHECK (household_size >= 1),
    poverty_guideline NUMERIC(12, 2) NOT NULL CHECK (poverty_guideline >= 0),
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (year, household_size)
);

-- Hospital-specific FAP thresholds
CREATE TABLE hospital_fap_thresholds (
    threshold_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    year INT NOT NULL,
    household_size INT NOT NULL CHECK (household_size >= 1),
    fpl_percentage NUMERIC(6, 2) NOT NULL CHECK (fpl_percentage >= 0 AND fpl_percentage <= 1000),
    coverage_type VARCHAR(50) DEFAULT 'full_charity', -- e.g., 'full_charity', 'discounted'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (hospital_id, year, household_size, fpl_percentage)
);

-- Families table: Stores applicant information (non-PHI until linked)
CREATE TABLE families (
    family_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_size INT NOT NULL CHECK (household_size >= 1),
    annual_gross_income NUMERIC(12, 2) NOT NULL CHECK (annual_gross_income >= 0),
    income_source VARCHAR(100),
    state CHAR(2) NOT NULL,
    cost_of_living_adjustment_factor NUMERIC(5, 3) DEFAULT 1.000, -- For future COL adjustments
    application_reference VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Eligibility assessments: Audit trail of all calculations
CREATE TABLE eligibility_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(family_id) ON DELETE CASCADE,
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    assessment_year INT NOT NULL,
    fpl_guideline NUMERIC(12, 2) NOT NULL,
    fpl_percentage NUMERIC(8, 4) NOT NULL,
    fap_threshold_applied NUMERIC(6, 2) NOT NULL,
    is_eligible BOOLEAN NOT NULL,
    coverage_type VARCHAR(50),
    notes TEXT,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculated_by VARCHAR(255)
);

-- Indexes for performance
CREATE INDEX idx_fpg_year_size ON federal_poverty_guidelines (year, household_size);
CREATE INDEX idx_hft_hospital_year ON hospital_fap_thresholds (hospital_id, year);
CREATE INDEX idx_ea_family ON eligibility_assessments (family_id);
CREATE INDEX idx_ea_hospital ON eligibility_assessments (hospital_id);

-- Comments for documentation
COMMENT ON TABLE hospitals IS 'Stores participating hospital information for charity care programs';
COMMENT ON TABLE federal_poverty_guidelines IS 'Annual Federal Poverty Guidelines published by HHS';
COMMENT ON TABLE hospital_fap_thresholds IS 'Hospital-specific Financial Assistance Policy thresholds based on FPL percentages';
COMMENT ON TABLE families IS 'Stores applicant household and income information';
COMMENT ON TABLE eligibility_assessments IS 'Audit trail of all charity care eligibility calculations';
