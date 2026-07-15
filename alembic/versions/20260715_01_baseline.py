"""Baseline existing ADS ERP schema.

Revision ID: 20260715_01
"""
from alembic import op
import sqlalchemy as sa

from app.models.base import Base

revision = "20260715_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Safe on both fresh and existing deployments; future revisions must use
    # explicit Alembic operations rather than create_all.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)
    bind = op.get_bind()
    count = bind.execute(sa.text("SELECT COUNT(*) FROM finance_expense_categories")).scalar()
    if not count:
        table = sa.table(
            "finance_expense_categories",
            sa.column("name", sa.String), sa.column("description", sa.String),
            sa.column("color", sa.String), sa.column("icon", sa.String),
            sa.column("display_order", sa.Integer), sa.column("is_active", sa.Boolean),
        )
        op.bulk_insert(table, [
            {"name": name, "description": None, "color": "#2563eb", "icon": "fas fa-receipt", "display_order": order, "is_active": True}
            for order, name in enumerate(["Fuel", "Electricity", "Salary", "Rent", "Maintenance", "Supplies", "Tax", "Other"], 1)
        ])


def downgrade():
    # A baseline must never destroy a pre-existing production schema.
    pass
