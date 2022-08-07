"""rename joined_at column

Revision ID: 3d8af65cd7df
Revises: 3d6e419ecf47
Create Date: 2022-08-07 20:00:35.191540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3d8af65cd7df"
down_revision = "3d6e419ecf47"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "joined", new_column_name="joined_at")


def downgrade() -> None:
    op.alter_column("users", "joined_at", new_column_name="joined")
