"""create a submission table

Revision ID: c7ae6a3d004a
Revises: 
Create Date: 2024-03-04 22:06:34.966512

"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import CheckConstraint

# revision identifiers, used by Alembic.
revision: str = 'c7ae6a3d004a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column(
            "status",
            sa.String(50),
            CheckConstraint("status IN ('pending', 'processed')"),
            nullable=False
        ),
        sa.Column("number_of_delivered_events", sa.Integer, nullable=False, default=0),
        sa.Column("sequence_number", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("submissions")
