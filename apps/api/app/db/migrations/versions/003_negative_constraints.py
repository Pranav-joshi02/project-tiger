"""Add negative constraints table for rejected claims

Revision ID: 003
Revises: 002
Create Date: 2026-08-17 19:52:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "negative_constraints" not in existing_tables:
        op.create_table(
            "negative_constraints",
            sa.Column("id", sa.Uuid, primary_key=True),
            sa.Column("tiger_id", sa.Uuid, sa.ForeignKey("tigers.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("image_id", sa.Uuid, sa.ForeignKey("images.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("flank_id", sa.Uuid, sa.ForeignKey("flanks.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("detection_id", sa.Uuid, sa.ForeignKey("detections.id", ondelete="SET NULL"), nullable=True),
            sa.Column("review_id", sa.Uuid, sa.ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("image_sha256", sa.String(64), nullable=True, index=True),
            sa.Column("reason", sa.String(500), nullable=True),
            sa.Column("reviewer_note", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "negative_constraints" in existing_tables:
        op.drop_table("negative_constraints")
