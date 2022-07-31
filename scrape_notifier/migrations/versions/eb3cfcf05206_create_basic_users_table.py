"""create basic users table

Revision ID: eb3cfcf05206
Revises: 
Create Date: 2022-07-31 10:48:19.508723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "eb3cfcf05206"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("users")
