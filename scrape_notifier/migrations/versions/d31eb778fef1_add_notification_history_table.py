"""add notification history table

Revision ID: d31eb778fef1
Revises: 3d8af65cd7df
Create Date: 2022-08-07 21:00:13.085051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d31eb778fef1"
down_revision = "3d8af65cd7df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "sent_notifications",
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("scrape_target", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("sent_at", "scrape_target"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("sent_notifications")
    # ### end Alembic commands ###
