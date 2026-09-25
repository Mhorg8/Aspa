"""Create the exercise catalog."""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0003"
down_revision: str | None = "20260924_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[datetime], sa.Column[datetime]]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "muscle_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name_fa", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_en"),
        sa.UniqueConstraint("name_fa"),
    )
    op.create_table(
        "equipment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name_fa", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_en"),
        sa.UniqueConstraint("name_fa"),
    )
    op.create_table(
        "exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name_fa", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=False),
        sa.Column("description_fa", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("equipment_id", sa.Uuid(), nullable=True),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("image_key", sa.String(length=500), nullable=True),
        sa.Column("video_key", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_exercises_difficulty",
        ),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exercises_equipment_id"), "exercises", ["equipment_id"])
    op.create_index(op.f("ix_exercises_is_active"), "exercises", ["is_active"])
    op.create_index(op.f("ix_exercises_name_en"), "exercises", ["name_en"])
    op.create_index(op.f("ix_exercises_name_fa"), "exercises", ["name_fa"])
    op.create_table(
        "exercise_muscles",
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("muscle_group_id", sa.Uuid(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_group_id"], ["muscle_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_group_id"),
    )


def downgrade() -> None:
    op.drop_table("exercise_muscles")
    op.drop_index(op.f("ix_exercises_name_fa"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_name_en"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_is_active"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_equipment_id"), table_name="exercises")
    op.drop_table("exercises")
    op.drop_table("equipment")
    op.drop_table("muscle_groups")
