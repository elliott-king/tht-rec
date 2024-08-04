"""initial tables

Revision ID: d1aba3846cea
Revises: 
Create Date: 2024-08-02 09:49:21.073232

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d1aba3846cea"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "restaurant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("restaurant", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_restaurant_name"), ["name"], unique=True)

    op.create_table(
        "restriction",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("restriction", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_restriction_name"), ["name"], unique=True)

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_name"), ["name"], unique=True)

    op.create_table(
        "restaurant_endorsement",
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
        sa.Column("restriction_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            "fk_restaurant_endorsement_restaurant_id",
        ),
        sa.ForeignKeyConstraint(
            ["restriction_id"],
            ["restriction.id"],
            "fk_restaurant_endorsement_restriction_id",
        ),
    )
    op.create_table(
        "table",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["restaurant_id"], ["restaurant.id"], "fk_table_restaurant_id"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_restriction",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("restriction_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["restriction_id"], ["restriction.id"], "fk_user_restriction_restriction_id"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], "fk_user_restriction_user_id"
        ),
    )
    op.create_table(
        "reservation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start", sa.DateTime(), nullable=False),
        sa.Column("end", sa.DateTime(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            "fk_reservation_restaurant_id",
        ),
        sa.ForeignKeyConstraint(["table_id"], ["table.id"], "fk_reservation_table_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("reservation")
    op.drop_table("user_restriction")
    op.drop_table("table")
    op.drop_table("restaurant_endorsement")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_name"))

    op.drop_table("user")
    with op.batch_alter_table("restriction", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_restriction_name"))

    op.drop_table("restriction")
    with op.batch_alter_table("restaurant", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_restaurant_name"))

    op.drop_table("restaurant")
    # ### end Alembic commands ###