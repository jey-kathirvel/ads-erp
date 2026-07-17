"""Add booking source for online and ERP bookings."""
from alembic import op
import sqlalchemy as sa

revision = "20260717_01"
down_revision = "20260715_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bookings",
        sa.Column("booking_source", sa.String(length=20), nullable=False, server_default="ERP"),
    )
    op.create_index("ix_bookings_booking_source", "bookings", ["booking_source"])
    op.add_column("bookings", sa.Column("subtotal_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bookings", sa.Column("gst_percent", sa.Numeric(5, 2), nullable=False, server_default="5"))
    op.add_column("bookings", sa.Column("gst_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.execute("UPDATE bookings SET subtotal_amount = total_amount, gst_amount = 0")
    op.add_column("bookings", sa.Column("email", sa.String(254), nullable=True))
    op.add_column("bookings", sa.Column("payment_expires_at", sa.DateTime(), nullable=True))
    op.add_column("bookings", sa.Column("provider_order_id", sa.String(100), nullable=True))
    op.create_index("ix_bookings_email", "bookings", ["email"])
    op.create_index("ix_bookings_payment_expires_at", "bookings", ["payment_expires_at"])
    op.create_index("ix_bookings_provider_order_id", "bookings", ["provider_order_id"], unique=True)


def downgrade():
    op.drop_index("ix_bookings_provider_order_id", table_name="bookings")
    op.drop_index("ix_bookings_payment_expires_at", table_name="bookings")
    op.drop_index("ix_bookings_email", table_name="bookings")
    op.drop_column("bookings", "provider_order_id")
    op.drop_column("bookings", "payment_expires_at")
    op.drop_column("bookings", "email")
    op.drop_column("bookings", "gst_amount")
    op.drop_column("bookings", "gst_percent")
    op.drop_column("bookings", "subtotal_amount")
    op.drop_index("ix_bookings_booking_source", table_name="bookings")
    op.drop_column("bookings", "booking_source")
