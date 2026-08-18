"""Add multi-part embeddings, body part embeddings table, and camera events table.

Revision ID: 001_multipart
Revises: None
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "001_multipart"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 1. Add multi-part embedding columns to embeddings table if not present
    if "embeddings" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("embeddings")]
        
        new_columns = [
            ("head_embedding", Vector(128)),
            ("flank_embedding", Vector(256)),
            ("hind_embedding", Vector(128)),
            ("visible_parts", sa.ARRAY(sa.String(20))),
            ("pose_confidence", sa.Float()),
            ("part_type", sa.String(20)),
            ("stripe_quality", sa.Float()),
            ("observation_id", sa.Uuid()),
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                op.add_column("embeddings", sa.Column(col_name, col_type, nullable=True))

        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_embeddings_head_hnsw "
            "ON embeddings USING hnsw (head_embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_embeddings_flank_hnsw "
            "ON embeddings USING hnsw (flank_embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_embeddings_hind_hnsw "
            "ON embeddings USING hnsw (hind_embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        )

    # 2. Create camera_events table if not exists
    if "camera_events" not in existing_tables:
        op.create_table(
            "camera_events",
            sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("station_id", sa.Uuid(), sa.ForeignKey("stations.id"), nullable=True),
            sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id"), nullable=True),
            sa.Column("encounter_id", sa.Uuid(), sa.ForeignKey("encounters.id"), nullable=True),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("frame_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("aggregated_embedding", Vector(512), nullable=True),
            sa.Column("aggregated_head_embedding", Vector(128), nullable=True),
            sa.Column("aggregated_flank_embedding", Vector(256), nullable=True),
            sa.Column("aggregated_hind_embedding", Vector(128), nullable=True),
            sa.Column("best_frame_id", sa.Uuid(), sa.ForeignKey("images.id"), nullable=True),
            sa.Column("best_frame_quality", sa.Float(), nullable=True),
            sa.Column("aggregation_strategy", sa.String(30), nullable=False, server_default="quality_weighted"),
            sa.Column("aggregation_confidence", sa.Float(), nullable=True),
            sa.Column("tiger_id", sa.Uuid(), sa.ForeignKey("tigers.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_camera_events_station", "camera_events", ["station_id"])
        op.create_index("ix_camera_events_tiger", "camera_events", ["tiger_id"])
        op.create_index("ix_camera_events_time", "camera_events", ["start_time"])

    # 3. Create body_part_embeddings table if not exists
    if "body_part_embeddings" not in existing_tables:
        op.create_table(
            "body_part_embeddings",
            sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("embedding_id", sa.Uuid(), sa.ForeignKey("embeddings.id", ondelete="CASCADE"), nullable=False),
            sa.Column("tiger_id", sa.Uuid(), sa.ForeignKey("tigers.id"), nullable=True),
            sa.Column("part_type", sa.String(20), nullable=False),
            sa.Column("vector", Vector(256), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("is_prototype", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("side", sa.String(10), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_body_part_emb_embedding", "body_part_embeddings", ["embedding_id"])
        op.create_index("ix_body_part_emb_tiger", "body_part_embeddings", ["tiger_id"])

    # 4. Add observation metadata columns if not present
    if "observations" in existing_tables:
        obs_cols = [c["name"] for c in inspector.get_columns("observations")]
        new_obs_cols = [
            ("global_similarity", sa.Float()),
            ("flank_similarity", sa.Float()),
            ("pose_compatibility", sa.Float()),
            ("quality_adjusted_score", sa.Float()),
            ("calibrated_confidence", sa.Float()),
            ("matching_parts", sa.Integer()),
            ("is_novel_detection", sa.Boolean()),
            ("camera_event_id", sa.Uuid()),
        ]
        for col_name, col_type in new_obs_cols:
            if col_name not in obs_cols:
                op.add_column("observations", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    pass
