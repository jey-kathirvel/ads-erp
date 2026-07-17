"""Prevent duplicate invoices for the same booking.

Revision ID: 20260717_03
Revises: 20260717_02
"""
from alembic import op
revision = "20260717_03"
down_revision = "20260717_02"
branch_labels = None
depends_on = None

def upgrade():
    op.create_index("uq_custom_gst_booking_invoice", "custom_gst_invoices", ["booking_id"], unique=True)

def downgrade():
    op.drop_index("uq_custom_gst_booking_invoice", table_name="custom_gst_invoices")
