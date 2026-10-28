"""create p2p services

Revision ID: 031aa92bee52
Revises: f48fc85bcc93
Create Date: 2026-10-28 23:36:15.675781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '031aa92bee52'
down_revision: Union[str, Sequence[str], None] = 'f48fc85bcc93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "p2p_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("local_ip", sa.String(15), nullable=False),
        sa.Column("local_port", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("fallback_enabled", sa.Boolean(), nullable=False),
        sa.Column("uid", sa.String(32), nullable=False),
        sa.Column("secret_key", sa.String(128), nullable=False),
        sa.UniqueConstraint("uid"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("p2p_services")
