"""add date to specify target at date

Revision ID: 1e8c09d980d6
Revises: d31eb778fef1
Create Date: 2022-08-12 13:28:37.528078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1e8c09d980d6"
down_revision = "d31eb778fef1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "sent_notifications",
        sa.Column("date_found", sa.Date(), nullable=False, server_default="1970-01-01"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("sent_notifications", "date_found")
    # ### end Alembic commands ###
