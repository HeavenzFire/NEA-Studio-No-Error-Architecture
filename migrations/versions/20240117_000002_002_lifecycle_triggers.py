"""FPL Charity Care Engine - Lifecycle Enforcement Triggers Migration

Migration ID: 002
Created: 2024-01-17
Purpose: Add database triggers for audit logging and lifecycle enforcement

This migration adds:
- Trigger to update updated_at timestamp on hospitals table
- Trigger to log all changes to hospital_fap_thresholds
- Function to validate FAP threshold consistency
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply lifecycle enforcement triggers."""
    
    # Create function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger on hospitals table
    op.execute("""
        CREATE TRIGGER trg_hospitals_update_timestamp
        BEFORE UPDATE ON hospitals
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create trigger on families table
    op.execute("""
        CREATE TRIGGER trg_families_update_timestamp
        BEFORE UPDATE ON families
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create audit log table for FAP threshold changes
    op.create_table(
        'fap_threshold_audit_log',
        sa.Column('audit_id', sa.UUID(), nullable=False),
        sa.Column('threshold_id', sa.UUID(), nullable=False),
        sa.Column('hospital_id', sa.UUID(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('household_size', sa.Integer(), nullable=False),
        sa.Column('old_fpl_percentage', sa.Numeric(6, 2)),
        sa.Column('new_fpl_percentage', sa.Numeric(6, 2)),
        sa.Column('old_coverage_type', sa.String(50)),
        sa.Column('new_coverage_type', sa.String(50)),
        sa.Column('old_notes', sa.TEXT()),
        sa.Column('new_notes', sa.TEXT()),
        sa.Column('change_type', sa.String(20), nullable=False),  -- INSERT, UPDATE, DELETE
        sa.Column('changed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        sa.Column('changed_by', sa.String(255), default=sa.func.current_setting('app.current_user', True)),
        sa.PrimaryKeyConstraint('audit_id')
    )
    
    # Create index on audit log
    op.create_index(
        'idx_fap_audit_threshold',
        'fap_threshold_audit_log',
        ['threshold_id']
    )
    op.create_index(
        'idx_fap_audit_hospital_year',
        'fap_threshold_audit_log',
        ['hospital_id', 'year']
    )
    
    # Create function to log FAP threshold changes
    op.execute("""
        CREATE OR REPLACE FUNCTION log_fap_threshold_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                INSERT INTO fap_threshold_audit_log (
                    audit_id, threshold_id, hospital_id, year, household_size,
                    new_fpl_percentage, new_coverage_type, new_notes,
                    change_type
                )
                VALUES (
                    uuid_generate_v4(), NEW.threshold_id, NEW.hospital_id, 
                    NEW.year, NEW.household_size,
                    NEW.fpl_percentage, NEW.coverage_type, NEW.notes,
                    'INSERT'
                );
                RETURN NEW;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO fap_threshold_audit_log (
                    audit_id, threshold_id, hospital_id, year, household_size,
                    old_fpl_percentage, new_fpl_percentage,
                    old_coverage_type, new_coverage_type,
                    old_notes, new_notes,
                    change_type
                )
                VALUES (
                    uuid_generate_v4(), NEW.threshold_id, NEW.hospital_id,
                    NEW.year, NEW.household_size,
                    OLD.fpl_percentage, NEW.fpl_percentage,
                    OLD.coverage_type, NEW.coverage_type,
                    OLD.notes, NEW.notes,
                    'UPDATE'
                );
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                INSERT INTO fap_threshold_audit_log (
                    audit_id, threshold_id, hospital_id, year, household_size,
                    old_fpl_percentage, old_coverage_type, old_notes,
                    change_type
                )
                VALUES (
                    uuid_generate_v4(), OLD.threshold_id, OLD.hospital_id,
                    OLD.year, OLD.household_size,
                    OLD.fpl_percentage, OLD.coverage_type, OLD.notes,
                    'DELETE'
                );
                RETURN OLD;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger on hospital_fap_thresholds table
    op.execute("""
        CREATE TRIGGER trg_fap_thresholds_audit
        AFTER INSERT OR UPDATE OR DELETE ON hospital_fap_thresholds
        FOR EACH ROW
        EXECUTE FUNCTION log_fap_threshold_changes();
    """)
    
    # Create function to validate FAP threshold consistency
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_fap_threshold_consistency()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Ensure coverage types follow logical order
            -- full_charity should have lower or equal FPL percentage than discounted
            IF NEW.coverage_type = 'full_charity' THEN
                PERFORM 1 FROM hospital_fap_thresholds
                WHERE hospital_id = NEW.hospital_id
                  AND year = NEW.year
                  AND household_size = NEW.household_size
                  AND fpl_percentage < NEW.fpl_percentage
                  AND coverage_type IN ('discounted', 'partial_discount');
                  
                IF FOUND THEN
                    RAISE EXCEPTION 'Full charity threshold must be at the lowest FPL percentage for hospital % in year %',
                        NEW.hospital_id, NEW.year;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create constraint trigger for FAP validation
    op.execute("""
        CREATE CONSTRAINT TRIGGER trg_fap_validate_consistency
        AFTER INSERT OR UPDATE ON hospital_fap_thresholds
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION validate_fap_threshold_consistency();
    """)
    
    # Add comment to audit log table
    op.execute("COMMENT ON TABLE fap_threshold_audit_log IS 'Immutable audit trail of all FAP threshold changes for compliance'")


def downgrade() -> None:
    """Rollback lifecycle enforcement triggers."""
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS trg_fap_validate_consistency ON hospital_fap_thresholds')
    op.execute('DROP TRIGGER IF EXISTS trg_fap_thresholds_audit ON hospital_fap_thresholds')
    op.execute('DROP TRIGGER IF EXISTS trg_families_update_timestamp ON families')
    op.execute('DROP TRIGGER IF EXISTS trg_hospitals_update_timestamp ON hospitals')
    
    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS validate_fap_threshold_consistency()')
    op.execute('DROP FUNCTION IF EXISTS log_fap_threshold_changes()')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop audit log table
    op.drop_table('fap_threshold_audit_log')
