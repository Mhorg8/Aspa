from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.modules.exercises.models import Exercise


class WorkoutPlan(TimestampMixin, Base):
    __tablename__ = "workout_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    days: Mapped[list[WorkoutPlanDay]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WorkoutPlanDay.position",
        lazy="selectin",
    )


class WorkoutPlanDay(TimestampMixin, Base):
    __tablename__ = "workout_plan_days"
    __table_args__ = (CheckConstraint("position >= 0", name="ck_workout_plan_days_position"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    plan: Mapped[WorkoutPlan] = relationship(back_populates="days")
    exercises: Mapped[list[WorkoutPlanExercise]] = relationship(
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="WorkoutPlanExercise.position",
        lazy="selectin",
    )


class WorkoutPlanExercise(TimestampMixin, Base):
    __tablename__ = "workout_plan_exercises"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_workout_plan_exercises_position"),
        CheckConstraint("sets BETWEEN 1 AND 20", name="ck_workout_plan_exercises_sets"),
        CheckConstraint("min_reps BETWEEN 1 AND 100", name="ck_workout_plan_exercises_min_reps"),
        CheckConstraint(
            "max_reps BETWEEN min_reps AND 100",
            name="ck_workout_plan_exercises_max_reps",
        ),
        CheckConstraint(
            "rest_seconds BETWEEN 0 AND 3600",
            name="ck_workout_plan_exercises_rest_seconds",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    day_id: Mapped[UUID] = mapped_column(
        ForeignKey("workout_plan_days.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_id: Mapped[UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    min_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    max_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    day: Mapped[WorkoutPlanDay] = relationship(back_populates="exercises")
    exercise: Mapped[Exercise] = relationship(lazy="joined")
