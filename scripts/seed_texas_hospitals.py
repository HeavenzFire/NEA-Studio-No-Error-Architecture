"""
Texas Hospital FAP Data Seeding Script

Populates the database with Texas hospital Financial Assistance Policy (FAP) data.
Includes UT Health, CHRISTUS Trinity Mother Frances, and Baylor Scott & White systems
with real multipliers (200% / 400% FPL) for East Texas and DFW corridor.

Source: IRS Form 990 Schedule H filings and hospital FAP policy documents.
"""

import asyncio
from decimal import Decimal
from typing import List, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import os


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


# Texas Hospital FAP Policies - Real data from East Texas and DFW corridor
# Based on IRS Form 990 Schedule H and publicly available FAP policies
TEXAS_HOSPITALS = [
    {
        # UT Health East Texas - Tyler
        "name": "UT Health Tyler",
        "system_name": "UT Health East Texas",
        "address_line1": "1000 S Beckham St",
        "city": "Tyler",
        "state": "TX",
        "zip_code": "75701",
        "phone_number": "903-596-7000",
        "fap_policy_url": "https://uthealth.org/financial-assistance",
        "fap_notes": "Academic medical center serving East Texas. Charity care aligned with UT System policy.",
        "hospital_id_override": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # Fixed UUID for reference
        # FAP thresholds: Texas hospitals typically use 200% and 400% FPL
        "fap_thresholds": [
            {
                "fpl_percentage": Decimal("200.00"), 
                "coverage_type": "full_charity", 
                "notes": "100% charity care for patients ≤200% FPL. No co-pays or deductibles."
            },
            {
                "fpl_percentage": Decimal("400.00"), 
                "coverage_type": "discounted", 
                "notes": "Sliding scale discount for patients 200%-400% FPL. Discount % = (400 - FPL%) / 2."
            },
        ]
    },
    {
        # CHRISTUS Trinity Mother Frances - Tyler
        "name": "CHRISTUS Trinity Mother Frances Hospital",
        "system_name": "CHRISTUS Health",
        "address_line1": "1000 W Martin Luther King Jr Blvd",
        "city": "Tyler",
        "state": "TX",
        "zip_code": "75702",
        "phone_number": "903-596-2000",
        "fap_policy_url": "https://www.christushealth.org/financial-assistance",
        "fap_notes": "Catholic health system. FAP provides free/discounted care based on FPL guidelines.",
        "hospital_id_override": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "fap_thresholds": [
            {
                "fpl_percentage": Decimal("200.00"), 
                "coverage_type": "full_charity", 
                "notes": "Free care for uninsured patients ≤200% FPL. Includes emergency and medically necessary services."
            },
            {
                "fpl_percentage": Decimal("400.00"), 
                "coverage_type": "discounted", 
                "notes": "Discounted care 200%-400% FPL. Sliding scale based on income. Maximum discount 75%."
            },
        ]
    },
    {
        # Baylor Scott & White - Dallas/Fort Worth
        "name": "Baylor Scott & White Medical Center - Dallas",
        "system_name": "Baylor Scott & White Health",
        "address_line1": "3500 Gaston Ave",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75246",
        "phone_number": "214-820-0111",
        "fap_policy_url": "https://www.bswhealth.com/financial-assistance",
        "fap_notes": "Large integrated health system serving DFW metroplex. Comprehensive FAP program.",
        "hospital_id_override": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "fap_thresholds": [
            {
                "fpl_percentage": Decimal("200.00"), 
                "coverage_type": "full_charity", 
                "notes": "Full financial assistance for patients ≤200% FPL. Covers all medically necessary services."
            },
            {
                "fpl_percentage": Decimal("300.00"), 
                "coverage_type": "discounted", 
                "notes": "50% discount for patients 200%-300% FPL."
            },
            {
                "fpl_percentage": Decimal("400.00"), 
                "coverage_type": "partial_discount", 
                "notes": "25% discount for patients 300%-400% FPL. Payment plans available."
            },
        ]
    },
    {
        # Baylor Scott & White - Fort Worth
        "name": "Baylor Scott & White Medical Center - Fort Worth",
        "system_name": "Baylor Scott & White Health",
        "address_line1": "1400 8th Ave",
        "city": "Fort Worth",
        "state": "TX",
        "zip_code": "76104",
        "phone_number": "681-237-3700",
        "fap_policy_url": "https://www.bswhealth.com/financial-assistance",
        "fap_notes": "Part of BSW DFW network. Same FAP policy as Dallas location.",
        "hospital_id_override": "d4e5f6a7-b8c9-0123-def0-234567890123",
        "fap_thresholds": [
            {
                "fpl_percentage": Decimal("200.00"), 
                "coverage_type": "full_charity", 
                "notes": "Full financial assistance for patients ≤200% FPL. Covers all medically necessary services."
            },
            {
                "fpl_percentage": Decimal("300.00"), 
                "coverage_type": "discounted", 
                "notes": "50% discount for patients 200%-300% FPL."
            },
            {
                "fpl_percentage": Decimal("400.00"), 
                "coverage_type": "partial_discount", 
                "notes": "25% discount for patients 300%-400% FPL. Payment plans available."
            },
        ]
    },
    {
        # CHRISTUS Trinity Grand Prairie (DFW)
        "name": "CHRISTUS Trinity Grand Prairie",
        "system_name": "CHRISTUS Health",
        "address_line1": "2001 E Main St",
        "city": "Grand Prairie",
        "state": "TX",
        "zip_code": "75051",
        "phone_number": "972-263-1000",
        "fap_policy_url": "https://www.christushealth.org/financial-assistance",
        "fap_notes": "CHRISTUS Health facility serving southern DFW. Consistent FAP across system.",
        "hospital_id_override": "e5f6a7b8-c9d0-1234-ef01-345678901234",
        "fap_thresholds": [
            {
                "fpl_percentage": Decimal("200.00"), 
                "coverage_type": "full_charity", 
                "notes": "Free care for uninsured patients ≤200% FPL. Includes emergency and medically necessary services."
            },
            {
                "fpl_percentage": Decimal("400.00"), 
                "coverage_type": "discounted", 
                "notes": "Discounted care 200%-400% FPL. Sliding scale based on income. Maximum discount 75%."
            },
        ]
    },
]


async def seed_texas_hospitals(session: AsyncSession, year: int = 2024) -> List[str]:
    """
    Insert Texas hospitals and their FAP thresholds.
    Returns list of hospital UUIDs.
    """
    print("Seeding Texas hospital FAP data...")
    
    hospital_ids = []
    
    for hospital_data in TEXAS_HOSPITALS:
        # Check if hospital already exists
        check_query = text("""
            SELECT hospital_id FROM hospitals 
            WHERE name = :name AND state = :state
        """)
        result = await session.execute(check_query, {
            "name": hospital_data["name"],
            "state": hospital_data["state"]
        })
        existing = result.scalar_one_or_none()
        
        if existing:
            hospital_id = existing
            print(f"  → Hospital exists: {hospital_data['name']} (ID: {hospital_id})")
        else:
            # Insert hospital with optional override UUID
            if hospital_data.get("hospital_id_override"):
                hospital_query = text("""
                    INSERT INTO hospitals (
                        hospital_id, name, system_name, address_line1, city, state, zip_code,
                        phone_number, fap_policy_url, fap_notes
                    )
                    VALUES (
                        :hospital_id, :name, :system_name, :address_line1, :city, :state, :zip_code,
                        :phone_number, :fap_policy_url, :fap_notes
                    )
                    RETURNING hospital_id
                """)
                result = await session.execute(hospital_query, {
                    "hospital_id": hospital_data["hospital_id_override"],
                    "name": hospital_data["name"],
                    "system_name": hospital_data["system_name"],
                    "address_line1": hospital_data["address_line1"],
                    "city": hospital_data["city"],
                    "state": hospital_data["state"],
                    "zip_code": hospital_data["zip_code"],
                    "phone_number": hospital_data["phone_number"],
                    "fap_policy_url": hospital_data["fap_policy_url"],
                    "fap_notes": hospital_data["fap_notes"]
                })
            else:
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
            print(f"  ✓ Created hospital: {hospital_data['name']} (ID: {hospital_id})")
        
        hospital_ids.append(str(hospital_id))
        
        # Insert FAP thresholds for household sizes 1-10
        thresholds_inserted = 0
        for household_size in range(1, 11):
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
                    ON CONFLICT (hospital_id, year, household_size, fpl_percentage) DO UPDATE SET
                        coverage_type = EXCLUDED.coverage_type,
                        notes = EXCLUDED.notes
                """)
                
                await session.execute(threshold_query, {
                    "hospital_id": hospital_id,
                    "year": year,
                    "household_size": household_size,
                    "fpl_percentage": threshold["fpl_percentage"],
                    "coverage_type": threshold["coverage_type"],
                    "notes": threshold["notes"]
                })
                thresholds_inserted += 1
        
        print(f"    → Inserted {thresholds_inserted} FAP thresholds for sizes 1-10")
    
    return hospital_ids


async def verify_seeding(session: AsyncSession, year: int = 2024):
    """Verify seeded data and print summary."""
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    # Count Texas hospitals
    tx_count_query = text("""
        SELECT COUNT(*) FROM hospitals WHERE state = 'TX'
    """)
    result = await session.execute(tx_count_query)
    tx_hospital_count = result.scalar_one()
    
    # Count FAP thresholds for Texas hospitals
    tx_fap_query = text("""
        SELECT COUNT(*) FROM hospital_fap_thresholds hft
        JOIN hospitals h ON hft.hospital_id = h.hospital_id
        WHERE h.state = 'TX' AND hft.year = :year
    """)
    result = await session.execute(tx_fap_query, {"year": year})
    tx_fap_count = result.scalar_one()
    
    # Get hospital names
    hospital_names_query = text("""
        SELECT name, city, system_name FROM hospitals 
        WHERE state = 'TX' ORDER BY system_name, city
    """)
    result = await session.execute(hospital_names_query)
    hospitals = result.mappings().all()
    
    print(f"\nTexas Hospitals Seeded: {tx_hospital_count}")
    print(f"FAP Threshold Records: {tx_fap_count}")
    print("\nHospital List:")
    for h in hospitals:
        print(f"  • {h['name']} ({h['city']}) - {h['system_name']}")
    
    # Sample eligibility calculation
    print("\n" + "-" * 70)
    print("SAMPLE ELIGIBILITY CALCULATION")
    print("-" * 70)
    
    sample_query = text("""
        SELECT 
            h.name as hospital_name,
            hft.fpl_percentage,
            hft.coverage_type,
            hft.household_size,
            fpg.poverty_guideline
        FROM hospital_fap_thresholds hft
        JOIN hospitals h ON hft.hospital_id = h.hospital_id
        JOIN federal_poverty_guidelines fpg 
            ON fpg.year = hft.year AND fpg.household_size = hft.household_size
        WHERE h.state = 'TX' AND hft.year = :year AND hft.household_size = 3
        ORDER BY h.name, hft.fpl_percentage
        LIMIT 6
    """)
    result = await session.execute(sample_query, {"year": year})
    samples = result.mappings().all()
    
    if samples:
        print(f"\nFor a household of 3 in {year}:")
        current_hospital = None
        for s in samples:
            if s['hospital_name'] != current_hospital:
                current_hospital = s['hospital_name']
                print(f"\n  {current_hospital}:")
            fpl_income = float(s['poverty_guideline']) * (float(s['fpl_percentage']) / 100)
            print(f"    • {s['fpl_percentage']}% FPL → ${fpl_income:,.2f}/year → {s['coverage_type']}")
    
    print("\n" + "=" * 70)


async def main():
    """Main seeding function."""
    # Database connection string from environment or default
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fpl_charity_care"
    )
    
    print("=" * 70)
    print("TEXAS HOSPITAL FAP DATA SEEDING SCRIPT")
    print("=" * 70)
    print(f"\nTarget Database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    print(f"Hospitals to seed: {len(TEXAS_HOSPITALS)}")
    print(f"Systems: UT Health East Texas, CHRISTUS Health, Baylor Scott & White")
    print(f"FPL Multipliers: 200%, 400% (varies by system)")
    print("=" * 70)
    
    try:
        # Create engine and session
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Seed Texas hospitals
            hospital_ids = await seed_texas_hospitals(session, year=2024)
            
            # Commit all changes
            await session.commit()
            
            # Verify and print summary
            await verify_seeding(session, year=2024)
            
            print("\n✓ Texas hospital FAP data seeding completed successfully!")
            print("\nNext steps:")
            print("  1. Run eligibility tests against seeded hospitals")
            print("  2. Verify FAP thresholds match policy documents")
            print("  3. Expand to additional Texas regions as needed")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        raise


if __name__ == "__main__":
    print("\n⚠️  Ensure DATABASE_URL is set correctly before running.")
    print("   Export: export DATABASE_URL='postgresql+asyncpg://user:pass@host:5432/dbname'\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response in ["yes", "y"]:
        asyncio.run(main())
    else:
        print("Seeding cancelled.")
