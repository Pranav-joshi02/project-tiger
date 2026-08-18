"""conservation platform

Revision ID: 002
Revises: 001_multipart
Create Date: 2026-08-17 19:04:28.000000
"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision = '002'
down_revision = '001_multipart'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Ensure extensions are present
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')

    # 1. merkle_audit_blocks
    if 'merkle_audit_blocks' not in existing_tables:
        op.create_table(
            'merkle_audit_blocks',
            sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('block_index', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.String(), nullable=False),
            sa.Column('previous_hash', sa.String(length=64), nullable=False),
            sa.Column('merkle_root', sa.String(length=64), nullable=False),
            sa.Column('records_hash', sa.String(length=64), nullable=False),
            sa.Column('signature', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_merkle_audit_blocks_block_index', 'merkle_audit_blocks', ['block_index'], unique=True)
        op.create_index('ix_merkle_audit_blocks_id', 'merkle_audit_blocks', ['id'], unique=False)

    # 2. tiger_fingerprints
    if 'tiger_fingerprints' not in existing_tables:
        op.create_table(
            'tiger_fingerprints',
            sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('tiger_id', sa.Uuid(), nullable=False),
            sa.Column('stripe_pattern_encoding', sa.JSON(), nullable=True, comment='Encoded stripe pattern features'),
            sa.Column('facial_features_encoding', sa.JSON(), nullable=True, comment='Encoded facial features'),
            sa.Column('flank_features_encoding', sa.JSON(), nullable=True, comment='Encoded flank features'),
            sa.Column('feature_dim', sa.Integer(), nullable=False, server_default='512'),
            sa.Column('model_version', sa.String(length=50), nullable=False),
            sa.Column('extraction_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('quality_score', sa.Float(), nullable=True, comment='0.0 to 1.0 confidence score of extraction'),
            sa.ForeignKeyConstraint(['tiger_id'], ['tigers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tiger_fingerprints_id', 'tiger_fingerprints', ['id'], unique=False)
        op.create_index('ix_tiger_fingerprints_tiger_id', 'tiger_fingerprints', ['tiger_id'], unique=False)

    # 3. behavior_logs
    if 'behavior_logs' not in existing_tables:
        op.create_table(
            'behavior_logs',
            sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('observation_id', sa.Uuid(), nullable=False),
            sa.Column('tiger_id', sa.Uuid(), nullable=True),
            sa.Column('behavior_class', sa.String(length=100), nullable=False, comment='e.g., resting, walking, hunting, mating'),
            sa.Column('confidence_score', sa.Float(), nullable=False),
            sa.Column('model_version', sa.String(length=50), nullable=False),
            sa.Column('temporal_context', sa.JSON(), nullable=True, comment='Sequence information if extracted from video'),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tiger_id'], ['tigers.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_behavior_logs_behavior_class', 'behavior_logs', ['behavior_class'], unique=False)
        op.create_index('ix_behavior_logs_id', 'behavior_logs', ['id'], unique=False)
        op.create_index('ix_behavior_logs_observation_id', 'behavior_logs', ['observation_id'], unique=False)
        op.create_index('ix_behavior_logs_tiger_id', 'behavior_logs', ['tiger_id'], unique=False)

    # 4. conflict_risk_zones
    if 'conflict_risk_zones' not in existing_tables:
        op.create_table(
            'conflict_risk_zones',
            sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
            sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
            sa.Column('zone_name', sa.String(length=200), nullable=True),
            sa.Column('risk_level', sa.String(length=50), nullable=False, comment='LOW, MEDIUM, HIGH, CRITICAL'),
            sa.Column('risk_score', sa.Float(), nullable=False),
            sa.Column('contributing_factors', sa.JSON(), nullable=True),
            sa.Column('model_version', sa.String(length=50), nullable=False),
            sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_conflict_risk_zones_id', 'conflict_risk_zones', ['id'], unique=False)
        op.create_index('ix_conflict_risk_zones_risk_level', 'conflict_risk_zones', ['risk_level'], unique=False)


def downgrade() -> None:
    pass
