"""Initial schema — users, reports, risk_zones, alerts + PostGIS

Revision ID: 0001
Revises:
Create Date: 2026-08-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ── users ────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TYPE userrole AS ENUM ('citizen', 'validator', 'authority')
    """)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("fcm_token", sa.String(512), nullable=True),
        sa.Column("role", sa.Enum("citizen", "validator", "authority", name="userrole"), nullable=False, server_default="citizen"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── reports ──────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TYPE reportstatus AS ENUM ('pending', 'validated', 'rejected')
    """)
    op.execute("""
        CREATE TYPE risklevel AS ENUM ('Low', 'Moderate', 'High', 'Critical', 'Unknown')
    """)
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("validated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("location", geoalchemy2.types.Geometry("POINT", srid=4326), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("elevation_m", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("media_urls", sa.JSON(), nullable=True, server_default="[]"),
        sa.Column("status", sa.Enum("pending", "validated", "rejected", name="reportstatus"), nullable=False, server_default="pending"),
        sa.Column("validator_notes", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.Enum("Low", "Moderate", "High", "Critical", "Unknown", name="risklevel"), nullable=False, server_default="Unknown"),
        sa.Column("rainfall_mm", sa.Float(), nullable=True),
        sa.Column("humidity_pct", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("risk_computed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.execute("CREATE INDEX ix_reports_location ON reports USING GIST (location)")

    # ── risk_zones ───────────────────────────────────────────────────────────
    op.create_table(
        "risk_zones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("boundary", geoalchemy2.types.Geometry("MULTIPOLYGON", srid=4326), nullable=False),
        sa.Column("centroid", geoalchemy2.types.Geometry("POINT", srid=4326), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="Unknown"),
        sa.Column("risk_score_avg", sa.Float(), nullable=True),
        sa.Column("risk_score_max", sa.Float(), nullable=True),
        sa.Column("report_ids", sa.JSON(), nullable=True, server_default="[]"),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True, server_default="{}"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute("CREATE INDEX ix_risk_zones_boundary ON risk_zones USING GIST (boundary)")
    op.execute("CREATE INDEX ix_risk_zones_centroid ON risk_zones USING GIST (centroid)")

    # ── soil_data ─────────────────────────────────────────────────────────────
    op.create_table(
        "soil_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("slope_deg", sa.Float(), nullable=False),
        sa.Column("elevation_m", sa.Float(), nullable=True),
        sa.Column("soil_saturation", sa.Float(), nullable=False),
        sa.Column("ndvi", sa.Float(), nullable=True),
        sa.Column("distance_to_water_km", sa.Float(), nullable=True),
    )

    # ── alerts ────────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE alertchannel AS ENUM ('sms', 'push', 'both')")
    op.execute("CREATE TYPE alertstatus AS ENUM ('pending', 'dispatching', 'completed', 'failed')")
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("authority_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("risk_zones.id"), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("channel", sa.Enum("sms", "push", "both", name="alertchannel"), nullable=False, server_default="both"),
        sa.Column("status", sa.Enum("pending", "dispatching", "completed", "failed", name="alertstatus"), nullable=False, server_default="pending"),
        sa.Column("geofence_wkt", sa.Text(), nullable=True),
        sa.Column("target_roles", sa.JSON(), nullable=True, server_default="[]"),
        sa.Column("recipient_count", sa.Integer(), server_default="0"),
        sa.Column("sms_sent", sa.Integer(), server_default="0"),
        sa.Column("push_sent", sa.Integer(), server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=True, server_default="[]"),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_authority_id", "alerts", ["authority_id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("soil_data")
    op.drop_table("risk_zones")
    op.drop_table("reports")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS alertchannel")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS reportstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
