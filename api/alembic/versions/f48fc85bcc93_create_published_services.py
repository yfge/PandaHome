"""create published services

Revision ID: f48fc85bcc93
Revises: 20251029_01
Create Date: 2026-10-28 23:28:19.756608

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f48fc85bcc93"
down_revision: Union[str, Sequence[str], None] = "20251029_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "published_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("local_ip", sa.String(15), nullable=False),
        sa.Column("local_port", sa.Integer(), nullable=False),
        sa.Column("public_port", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(3), nullable=False),
        sa.Column("mode", sa.String(6), nullable=False),
        sa.Column("domain", sa.String(253), nullable=False),
        sa.Column("rr", sa.String(253), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("lease_duration", sa.Integer(), nullable=False),
        sa.Column("owner_token", sa.String(32), nullable=False),
        sa.Column("runtime", sa.JSON(), nullable=False),
        sa.UniqueConstraint("public_port", "protocol", name="uq_published_port_protocol"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("published_services")
