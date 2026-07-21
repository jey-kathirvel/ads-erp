"""create hotel laundry tables

Revision ID: 6c425b8c5dc9
Revises: 20260717_03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c425b8c5dc9"
down_revision: Union[str, None] = "20260717_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hotel_laundry_batches",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "batch_no",
            sa.String(length=40),
            nullable=False,
        ),

        sa.Column(
            "batch_date",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "source_type",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "room_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "booking_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "vendor_name",
            sa.String(length=120),
            nullable=True,
        ),

        sa.Column(
            "sent_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "expected_return_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "returned_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "total_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "clean_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "damaged_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "missing_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "remarks",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_by",
            sa.String(length=120),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
            ondelete="SET NULL",
        ),

        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "batch_no",
            name="uq_hotel_laundry_batches_batch_no",
        ),
    )

    op.create_index(
        "ix_hotel_laundry_batches_id",
        "hotel_laundry_batches",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_batch_no",
        "hotel_laundry_batches",
        ["batch_no"],
        unique=True,
    )

    op.create_index(
        "ix_hotel_laundry_batches_batch_date",
        "hotel_laundry_batches",
        ["batch_date"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_source_type",
        "hotel_laundry_batches",
        ["source_type"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_room_id",
        "hotel_laundry_batches",
        ["room_id"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_booking_id",
        "hotel_laundry_batches",
        ["booking_id"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_status",
        "hotel_laundry_batches",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_vendor_name",
        "hotel_laundry_batches",
        ["vendor_name"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_sent_at",
        "hotel_laundry_batches",
        ["sent_at"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_expected_return_at",
        "hotel_laundry_batches",
        ["expected_return_at"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_returned_at",
        "hotel_laundry_batches",
        ["returned_at"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batches_created_at",
        "hotel_laundry_batches",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "hotel_laundry_batch_items",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "laundry_batch_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "inventory_item_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "issued_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "returned_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "clean_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "damaged_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "missing_quantity",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),

        sa.Column(
            "remarks",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["laundry_batch_id"],
            ["hotel_laundry_batches.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["inventory_item_id"],
            ["hotel_inventory_items.id"],
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "laundry_batch_id",
            "inventory_item_id",
            name="uq_hotel_laundry_batch_item",
        ),
    )

    op.create_index(
        "ix_hotel_laundry_batch_items_id",
        "hotel_laundry_batch_items",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batch_items_laundry_batch_id",
        "hotel_laundry_batch_items",
        ["laundry_batch_id"],
        unique=False,
    )

    op.create_index(
        "ix_hotel_laundry_batch_items_inventory_item_id",
        "hotel_laundry_batch_items",
        ["inventory_item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_hotel_laundry_batch_items_inventory_item_id",
        table_name="hotel_laundry_batch_items",
    )

    op.drop_index(
        "ix_hotel_laundry_batch_items_laundry_batch_id",
        table_name="hotel_laundry_batch_items",
    )

    op.drop_index(
        "ix_hotel_laundry_batch_items_id",
        table_name="hotel_laundry_batch_items",
    )

    op.drop_table(
        "hotel_laundry_batch_items"
    )

    op.drop_index(
        "ix_hotel_laundry_batches_created_at",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_returned_at",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_expected_return_at",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_sent_at",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_vendor_name",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_status",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_booking_id",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_room_id",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_source_type",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_batch_date",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_batch_no",
        table_name="hotel_laundry_batches",
    )

    op.drop_index(
        "ix_hotel_laundry_batches_id",
        table_name="hotel_laundry_batches",
    )

    op.drop_table(
        "hotel_laundry_batches"
    )
