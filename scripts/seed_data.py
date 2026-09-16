"""
Data Seeding Script for FPL Charity Care Engine

Populates the database with Federal Poverty Guidelines and sample hospital data.
Run this script after creating the database schema to initialize reference data.
"""

import asyncio
from decimal import Decimal
from typing import List, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text


# 2024 Federal Poverty Guidelines (48 contiguous states + DC)
# Source: U.S. Department of Health & Human Services
# https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines
FPL_2024_DATA = {
    1: Decimal("15060.00"),
    2: Decimal("20440.00"),
    3: Decimal("25820.00"),
    4: Decimal("31200.00"),
    5: Decimal("36580.00"),
    6: Decimal("41960.00"),
    7: Decimal("47340.00"),
    8: Decimal("52720.00"),
}

# Additional household sizes (add $5,380 for each additional person)
def calculate_fpl_for_size(household_size: int, base_4_person: Decimal = Decimal("31200.00")) -> Decimal:
    """Calculate FPL for household sizes > 8."""
    if household_size <= 4:
        return FPL_2024_DATA.get(household_size, base_4_person)
    else:
        additional_people = household_size - 4
        return base_4_person + (additional_people * Decimal("5380.00"))


# Sample hospital FAP policies (Financial Assistance Policies)
SAMPLE_HOSPITALS = [
    {
        "name": "General Community Hospital",
        "system_name": "Community Health System",
        "address_line1": "123 Healthcare Drive",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
        "phone_number": "555-123-4567",
        "fap_policy_url": "https://example.com/fap-policy",
        "fap_notes": "Standard community hospital FAP",
        # FAP thresholds: percentage of FPL and coverage type
        "fap_thresholds": [
            {"fpl_percentage": Decimal("200.00"), "coverage_type": "full_charity", "notes": "100% charity care up to 200% FPL"},
            {"fpl_percentage": Decimal("300.00"), "coverage_type": "discounted", "notes": "Sliding scale discount 200-300% FPL"},
            {"fpl_percentage": Decimal("400.00"), "coverage_type": "partial_discount", "notes": "Limited assistance 300-400% FPL"},
        ]
    },
    {
        "name": "Metro Medical Center",
        "system_name": "Metro Health Network",
        "address_line1": "456 Wellness Boulevard",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "phone_number": "555-987-6543",
        "fap_policy_url": "https://example.com/metro-fap",
        "fap_notes": "Urban medical center with expanded coverage",
        "fap_thresholds": [
            {"fpl_percentage": Decimal("250.00"), "coverage_type": "full_charity", "notes": "Generous full charity up to 250% FPL"},
            {"fpl_percentage": Decimal("500.00"), "coverage_type": "discounted", "notes": "Extended sliding scale up to 500% FPL"},
        ]
    },
    {
        "name": "Rural Access Hospital",
        "system_name": "Independent",
        "address_line1": "789 Country Road",
        "city": "Smalltown",
        "state": "IA",
        "zip_code": "50001",
        "phone_number": "555-456-7890",
        "fap_policy_url": "https://example.com/rural-fap",
        "fap_notes": "Rural hospital with limited but essential coverage",
        "fap_thresholds": [
            {"fpl_percentage": Decimal("150.00"), "coverage_type": "full_charity", "notes": "Basic charity care up to 150% FPL"},
            {"fpl_percentage": Decimal("250.00"), "coverage_type": "discounted", "notes": "Discounted care 150-250% FPL"},
        ]
    }
]


async def seed_fpl_guidelines(session: AsyncSession, year: int = 2024):
    """Insert Federal Poverty Guidelines for a given year."""
    print(f"Seeding FPL guidelines for {year}...")
    
    for household_size in range(1, 11):  # Sizes 1-10
        fpl_amount = calculate_fpl_for_size(household_size)
        
        query = text("""
            INSERT INTO federal_poverty_guidelines (year, household_size, poverty_guideline, source_url)
            VALUES (:year, :household_size, :poverty_guideline, :source_url)
            ON CONFLICT (year, household_size) DO UPDATE SET
                poverty_guideline = EXCLUDED.poverty_guideline,
                source_url = EXCLUDED.source_url
        """)
        
        await session.execute(query, {
            "year": year,
            "household_size": household_size,
            "poverty_guideline": fpl_amount,
            "source_url": "https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines"
        })
    
    print(f"✓ Inserted FPL guidelines for household sizes 1-10")


async def seed_hospitals(session: AsyncSession) -> List[str]:
    """Insert sample hospitals and their FAP thresholds. Returns list of hospital UUIDs."""
    print("Seeding hospital data...")
    
    hospital_ids = []
    
    for hospital_data in SAMPLE_HOSPITALS:
        # Insert hospital
        hospital_query = text("""
            INSERT INTO hospitals (
                name, system_name, address_line1, city, state, zip_code,
                phone_number, fap_policy_url, fap_notes
            )
            VALUES (
                :name, :system_name, :address_line1, :city, :state, :zip_code,
                :phone_number, :fap_policy_url, :fap_notes
            )
            RETURNING hospital_id
        """)
        
        result = await session.execute(hospital_query, hospital_data)
        hospital_id = result.scalar_one()
        hospital_ids.append(str(hospital_id))
        
        print(f"  ✓ Created hospital: {hospital_data['name']} (ID: {hospital_id})")
        
        # Insert FAP thresholds for household sizes 1-8
        for household_size in range(1, 9):
            for threshold in hospital_data["fap_thresholds"]:
                threshold_query = text("""
                    INSERT INTO hospital_fap_thresholds (
                        hospital_id, year, household_size, fpl_percentage,
                        coverage_type, notes
                    )
                    VALUES (
                        :hospital_id, :year, :household_size, :fpl_percentage,
                        :coverage_type, :notes
                    )
                    ON CONFLICT (hospital_id, year, household_size, fpl_percentage) DO NOTHING
                """)
                
                await session.execute(threshold_query, {
                    "hospital_id": hospital_id,
                    "year": 2024,
                    "household_size": household_size,
                    "fpl_percentage": threshold["fpl_percentage"],
                    "coverage_type": threshold["coverage_type"],
                    "notes": threshold["notes"]
                })
    
    print(f"✓ Created {len(hospital_ids)} hospitals with FAP thresholds")
    return hospital_ids


async def main():
    """Main seeding function."""
    # Database connection string - update with your actual database URL
    DATABASE_URL = "postgresql+asyncpg://username:password@localhost:5432/fpl_charity_care"
    
    print("=" * 60)
    print("FPL Charity Care Engine - Data Seeding Script")
    print("=" * 60)
    
    try:
        # Create engine and session
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Seed FPL guidelines
            await seed_fpl_guidelines(session, year=2024)
            
            # Seed hospitals
            hospital_ids = await seed_hospitals(session)
            
            # Commit all changes
            await session.commit()
            
            print("\n" + "=" * 60)
            print("✓ Seeding completed successfully!")
            print("=" * 60)
            print(f"\nCreated {len(SAMPLE_HOSPITALS)} hospitals:")
            for i, hospital in enumerate(SAMPLE_HOSPITALS):
                print(f"  {i+1}. {hospital['name']} - ID: {hospital_ids[i]}")
            print("\nFPL Guidelines loaded for 2024 (household sizes 1-10)")
            print("\nYou can now run the eligibility engine with this data.")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        raise


if __name__ == "__main__":
    # Note: Update DATABASE_URL before running
    print("\n⚠️  IMPORTANT: Update the DATABASE_URL in this script before running!")
    print("   Default: postgresql+asyncpg://username:password@localhost:5432/fpl_charity_care\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response in ["yes", "y"]:
        asyncio.run(main())
    else:
        print("Seeding cancelled.")
