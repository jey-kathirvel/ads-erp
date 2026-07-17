"""Extend hotel GST invoices with booking, customer, and payment snapshots.

Revision ID: 20260717_02
Revises: 20260717_01
"""
from alembic import op
import sqlalchemy as sa
revision = "20260717_02"
down_revision = "20260717_01"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("custom_gst_invoices", sa.Column("booking_id", sa.Integer(), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("booking_no", sa.String(40), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("invoice_date", sa.Date(), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("customer_email", sa.String(254), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("number_of_rooms", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("custom_gst_invoices", sa.Column("additional_items_json", sa.Text(), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("discount_amount", sa.Numeric(12,2), nullable=False, server_default="0"))
    op.add_column("custom_gst_invoices", sa.Column("payment_mode", sa.String(50), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("payment_reference", sa.String(120), nullable=True))
    op.add_column("custom_gst_invoices", sa.Column("amount_paid", sa.Numeric(12,2), nullable=False, server_default="0"))
    op.add_column("custom_gst_invoices", sa.Column("balance_amount", sa.Numeric(12,2), nullable=False, server_default="0"))
    op.add_column("custom_gst_invoices", sa.Column("notes", sa.Text(), nullable=True))
    op.create_foreign_key("fk_custom_gst_booking", "custom_gst_invoices", "bookings", ["booking_id"], ["id"])
    op.create_index("ix_custom_gst_booking_id", "custom_gst_invoices", ["booking_id"])
    op.create_index("ix_custom_gst_booking_no", "custom_gst_invoices", ["booking_no"])
    op.execute("UPDATE custom_gst_invoices SET invoice_date = CAST(created_at AS date) WHERE invoice_date IS NULL")
    op.alter_column("custom_gst_invoices", "invoice_date", nullable=False)

def downgrade():
    op.drop_index("ix_custom_gst_booking_no", table_name="custom_gst_invoices")
    op.drop_index("ix_custom_gst_booking_id", table_name="custom_gst_invoices")
    op.drop_constraint("fk_custom_gst_booking", "custom_gst_invoices", type_="foreignkey")
    for name in ["notes","balance_amount","amount_paid","payment_reference","payment_mode","discount_amount","additional_items_json","number_of_rooms","customer_email","invoice_date","booking_no","booking_id"]:
        op.drop_column("custom_gst_invoices", name)
