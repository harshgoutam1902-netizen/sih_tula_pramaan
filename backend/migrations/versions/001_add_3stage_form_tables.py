"""Add 3-stage form system tables

Revision ID: 001_3stage_form
Revises: 
Create Date: 2026-09-28

Adds tables for:
- Extended instrument_profiles
- class_determinations
- test_plans
- environment_sessions
- environment_readings

DEMO PROTOTYPE: SQLite-compatible version (uses JSON instead of JSONB)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_3stage_form'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== Extend instrument_profiles table ==========
    # Assuming instrument_profiles table exists from previous migrations
    # Add classification and category parameters
    
    op.add_column('instrument_profiles',
        sa.Column('e', sa.DECIMAL(10, 6), nullable=True, comment='Verification scale interval (grams)')
    )
    op.add_column('instrument_profiles',
        sa.Column('max_capacity', sa.DECIMAL(12, 3), nullable=True, comment='Maximum capacity (kg)')
    )
    op.add_column('instrument_profiles',
        sa.Column('min_capacity', sa.DECIMAL(12, 3), nullable=True, comment='Minimum capacity (kg)')
    )
    op.add_column('instrument_profiles',
        sa.Column('is_multi_range', sa.Boolean(), default=False, nullable=False)
    )
    op.add_column('instrument_profiles',
        sa.Column('is_multi_interval', sa.Boolean(), default=False, nullable=False)
    )
    op.add_column('instrument_profiles',
        sa.Column('sub_ranges', sa.JSON(), nullable=True, comment='Array of {e, max_cap, min_cap}')
    )
    op.add_column('instrument_profiles',
        sa.Column('self_indicating_type', sa.String(30), nullable=True)
    )
    op.add_column('instrument_profiles',
        sa.Column('indication_type', sa.String(20), nullable=True)
    )
    op.add_column('instrument_profiles',
        sa.Column('is_electronic', sa.Boolean(), nullable=True)
    )
    op.add_column('instrument_profiles',
        sa.Column('has_tare_device', sa.Boolean(), nullable=True)
    )
    op.add_column('instrument_profiles',
        sa.Column('intended_use', sa.String(30), nullable=True)
    )
    
    # Add CHECK constraints for enum-like fields
    op.create_check_constraint(
        'ck_self_indicating_type',
        'instrument_profiles',
        sa.text("self_indicating_type IN ('self_indicating', 'semi_self_indicating', 'non_self_indicating')")
    )
    op.create_check_constraint(
        'ck_indication_type',
        'instrument_profiles',
        sa.text("indication_type IN ('digital', 'analogue')")
    )
    op.create_check_constraint(
        'ck_intended_use',
        'instrument_profiles',
        sa.text("intended_use IN ('general_trade', 'direct_sales', 'price_computing', 'labelling', 'grading')")
    )
    
    # ========== class_determinations table ==========
    op.create_table(
        'class_determinations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('instrument_profile_id', sa.Integer(), sa.ForeignKey('instrument_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rulepack_version', sa.String(50), nullable=False, comment='Pinned rulepack version (e.g., R76-1:2006)'),
        sa.Column('computed_n', sa.DECIMAL(12, 6), nullable=False, comment='Calculated n = Max / e'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('determined_class', sa.String(10), nullable=True),
        sa.Column('candidates', sa.JSON(), nullable=True, comment='For AMBIGUOUS status'),
        sa.Column('confirmed_by', sa.Integer(), nullable=True, comment='User ID who confirmed'),
        sa.Column('override_reason', sa.Text(), nullable=True, comment='Required for AMBIGUOUS confirmations'),
        sa.Column('confirmed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('instrument_profile_id', 'rulepack_version', name='uq_class_det_profile_version'),
        comment='Classification determinations with human confirmation'
    )
    
    # CHECK constraint for status
    op.create_check_constraint(
        'ck_class_det_status',
        'class_determinations',
        sa.text("status IN ('DETERMINED', 'AMBIGUOUS', 'INVALID')")
    )
    
    # Indexes
    op.create_index('idx_class_det_profile', 'class_determinations', ['instrument_profile_id'])
    op.create_index('idx_class_det_status', 'class_determinations', ['status'])
    op.create_index('idx_class_det_rulepack', 'class_determinations', ['rulepack_version'])
    
    # ========== test_plans table ==========
    op.create_table(
        'test_plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_job_id', sa.Integer(), nullable=False, comment='Foreign key to test_jobs table'),
        sa.Column('rulepack_version', sa.String(50), nullable=False),
        sa.Column('tests', sa.JSON(), nullable=False, comment='Array of resolved test objects'),
        sa.Column('class', sa.String(10), nullable=False, name='class_'),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('test_job_id', name='uq_test_plan_job'),
        comment='Assembled test plans with resolved variants'
    )
    
    op.create_index('idx_test_plan_job', 'test_plans', ['test_job_id'])
    op.create_index('idx_test_plan_class', 'test_plans', ['class_'])
    
    # ========== environment_sessions table ==========
    op.create_table(
        'environment_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_job_id', sa.Integer(), nullable=False),
        sa.Column('start_temp', sa.DECIMAL(5, 2), nullable=False, comment='Temperature (°C)'),
        sa.Column('start_rel_h', sa.DECIMAL(5, 2), nullable=False, comment='Relative humidity (%)'),
        sa.Column('start_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('start_bar_pres', sa.DECIMAL(7, 2), nullable=False, comment='Barometric pressure (hPa)'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('test_job_id', name='uq_env_session_job'),
        comment='Session-start environment conditions'
    )
    
    op.create_index('idx_env_session_job', 'environment_sessions', ['test_job_id'])
    
    # ========== environment_readings table ==========
    op.create_table(
        'environment_readings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_run_id', sa.Integer(), nullable=False, comment='Foreign key to test_runs table'),
        sa.Column('checkpoint', sa.String(10), nullable=False),
        sa.Column('temp', sa.DECIMAL(5, 2), nullable=False),
        sa.Column('rel_h', sa.DECIMAL(5, 2), nullable=False),
        sa.Column('time', sa.TIMESTAMP(), nullable=False),
        sa.Column('bar_pres', sa.DECIMAL(7, 2), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), onupdate=sa.func.now(), nullable=True),
        sa.UniqueConstraint('test_run_id', 'checkpoint', name='uq_env_reading_test_checkpoint'),
        comment='Per-test environment readings with auto-carry tracking'
    )
    
    # CHECK constraints
    op.create_check_constraint(
        'ck_env_reading_checkpoint',
        'environment_readings',
        sa.text("checkpoint IN ('start', 'max', 'end')")
    )
    op.create_check_constraint(
        'ck_env_reading_source',
        'environment_readings',
        sa.text("source IN ('auto_carried', 'manual_override')")
    )
    
    op.create_index('idx_env_reading_test', 'environment_readings', ['test_run_id'])
    op.create_index('idx_env_reading_checkpoint', 'environment_readings', ['checkpoint'])


def downgrade() -> None:
    # Drop tables in reverse order (respect foreign keys)
    op.drop_table('environment_readings')
    op.drop_table('environment_sessions')
    op.drop_table('test_plans')
    op.drop_table('class_determinations')
    
    # Drop added columns from instrument_profiles
    op.drop_constraint('ck_intended_use', 'instrument_profiles', type_='check')
    op.drop_constraint('ck_indication_type', 'instrument_profiles', type_='check')
    op.drop_constraint('ck_self_indicating_type', 'instrument_profiles', type_='check')
    
    op.drop_column('instrument_profiles', 'intended_use')
    op.drop_column('instrument_profiles', 'has_tare_device')
    op.drop_column('instrument_profiles', 'is_electronic')
    op.drop_column('instrument_profiles', 'indication_type')
    op.drop_column('instrument_profiles', 'self_indicating_type')
    op.drop_column('instrument_profiles', 'sub_ranges')
    op.drop_column('instrument_profiles', 'is_multi_interval')
    op.drop_column('instrument_profiles', 'is_multi_range')
    op.drop_column('instrument_profiles', 'min_capacity')
    op.drop_column('instrument_profiles', 'max_capacity')
    op.drop_column('instrument_profiles', 'e')
