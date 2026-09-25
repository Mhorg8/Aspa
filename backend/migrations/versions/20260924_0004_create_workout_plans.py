"""Create workout plan tables."""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0004"
down_revision: str | None = "20260924_0003"
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
        "workout_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workout_plans_is_archived"), "workout_plans", ["is_archived"])
    op.create_index(op.f("ix_workout_plans_user_id"), "workout_plans", ["user_id"])
    op.create_table(
        "workout_plan_days",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("position >= 0", name="ck_workout_plan_days_position"),
        sa.ForeignKeyConstraint(["plan_id"], ["workout_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workout_plan_days_plan_id"), "workout_plan_days", ["plan_id"])
    op.create_table(
        "workout_plan_exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("day_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("min_reps", sa.Integer(), nullable=False),
        sa.Column("max_reps", sa.Integer(), nullable=False),
        sa.Column("rest_seconds", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("position >= 0", name="ck_workout_plan_exercises_position"),
        sa.CheckConstraint("sets BETWEEN 1 AND 20", name="ck_workout_plan_exercises_sets"),
        sa.CheckConstraint(
            "min_reps BETWEEN 1 AND 100",
            name="ck_workout_plan_exercises_min_reps",
        ),
        sa.CheckConstraint(
            "max_reps BETWEEN min_reps AND 100",
            name="ck_workout_plan_exercises_max_reps",
        ),
        sa.CheckConstraint(
            "rest_seconds BETWEEN 0 AND 3600",
            name="ck_workout_plan_exercises_rest_seconds",
        ),
        sa.ForeignKeyConstraint(["day_id"], ["workout_plan_days.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workout_plan_exercises_day_id"), "workout_plan_exercises", ["day_id"])
    op.create_index(
        op.f("ix_workout_plan_exercises_exercise_id"),
        "workout_plan_exercises",
        ["exercise_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workout_plan_exercises_exercise_id"),
        table_name="workout_plan_exercises",
    )
    op.drop_index(op.f("ix_workout_plan_exercises_day_id"), table_name="workout_plan_exercises")
    op.drop_table("workout_plan_exercises")
    op.drop_index(op.f("ix_workout_plan_days_plan_id"), table_name="workout_plan_days")
    op.drop_table("workout_plan_days")
    op.drop_index(op.f("ix_workout_plans_user_id"), table_name="workout_plans")
    op.drop_index(op.f("ix_workout_plans_is_archived"), table_name="workout_plans")
    op.drop_table("workout_plans")
