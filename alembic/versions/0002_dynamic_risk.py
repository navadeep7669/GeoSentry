"""Add dynamic risk fields and risk observation time series.

This migration extends the existing Hackbros schema; it deliberately does
not create duplicate users/reports/risk_zones/alerts tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Extend existing risk_zones table.
    op.add_column("risk_zones", sa.Column("external_id", sa.String(100), nullable=True))
    op.add_column("risk_zones", sa.Column("environmental_risk", sa.Float(), nullable=True))
    op.add_column("risk_zones", sa.Column("exposure_score", sa.Float(), nullable=True))
    op.add_column("risk_zones", sa.Column("priority_score", sa.Float(), nullable=True))
    op.add_column("risk_zones", sa.Column("reasons", sa.JSON(), nullable=True))
    op.add_column("risk_zones", sa.Column("recommended_action", sa.Text(), nullable=True))
    op.add_column("risk_zones", sa.Column("last_hazard_probability", sa.Float(), nullable=True))
    op.add_column("risk_zones", sa.Column("field_report_count", sa.Integer(), nullable=False, server_default="0"))

    op.create_index("ix_risk_zones_external_id", "risk_zones", ["external_id"])
    op.create_index("ix_risk_zones_priority_score", "risk_zones", ["priority_score"])

    # Time-series observations for continuous monitoring.
    op.create_table(
        "risk_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("zone_id", sa.Integer(), nullable=False, index=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("location", geoalchemy2.types.Geometry("POINT", srid=4326), nullable=False),
        sa.Column("rainfall_24h_mm", sa.Float()),
        sa.Column("rainfall_7d_mm", sa.Float()),
        sa.Column("soil_saturation", sa.Float()),
        sa.Column("slope_deg", sa.Float()),
        sa.Column("satellite_change", sa.Float()),
        sa.Column("historical_susceptibility", sa.Float()),
        sa.Column("population_exposure", sa.Float()),
        sa.Column("road_importance", sa.Float()),
        sa.Column("critical_infrastructure", sa.Float()),
        sa.Column("rate_of_change", sa.Float()),
        sa.Column("model_probability", sa.Float()),
        sa.Column("hazard_probability", sa.Float()),
        sa.Column("environmental_risk", sa.Float()),
        sa.Column("exposure_score", sa.Float()),
        sa.Column("priority_score", sa.Float()),
        sa.Column("risk_level", sa.String(20)),
        sa.Column("reasons", sa.Text()),
        sa.Column("recommended_action", sa.Text()),
    )
    op.create_index(
        "ix_risk_observations_location",
        "risk_observations",
        ["location"],
        postgresql_using="gist",
    )
    op.create_index(
        "ix_risk_observations_zone_observed",
        "risk_observations",
        ["zone_id", "observed_at"],
    )

def downgrade() -> None:
    op.drop_index("ix_risk_observations_zone_observed", table_name="risk_observations")
    op.drop_index("ix_risk_observations_location", table_name="risk_observations")
    op.drop_table("risk_observations")

    op.drop_index("ix_risk_zones_priority_score", table_name="risk_zones")
    op.drop_index("ix_risk_zones_external_id", table_name="risk_zones")
    op.drop_column("risk_zones", "field_report_count")
    op.drop_column("risk_zones", "last_hazard_probability")
    op.drop_column("risk_zones", "recommended_action")
    op.drop_column("risk_zones", "reasons")
    op.drop_column("risk_zones", "priority_score")
    op.drop_column("risk_zones", "exposure_score")
    op.drop_column("risk_zones", "environmental_risk")
    op.drop_column("risk_zones", "external_id")
