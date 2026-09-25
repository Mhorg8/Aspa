from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.exercises.models import Exercise
from app.modules.workout_plans.models import (
    WorkoutPlan,
    WorkoutPlanDay,
    WorkoutPlanExercise,
)


class WorkoutPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_owned(self, user_id: UUID, *, include_archived: bool) -> list[WorkoutPlan]:
        statement = select(WorkoutPlan).where(WorkoutPlan.user_id == user_id)
        if not include_archived:
            statement = statement.where(WorkoutPlan.is_archived.is_(False))
        result = await self.session.scalars(
            statement.options(
                selectinload(WorkoutPlan.days)
                .selectinload(WorkoutPlanDay.exercises)
                .joinedload(WorkoutPlanExercise.exercise)
            ).order_by(WorkoutPlan.updated_at.desc(), WorkoutPlan.id)
        )
        return list(result.all())

    async def get_owned(self, plan_id: UUID, user_id: UUID) -> WorkoutPlan | None:
        return await self.session.scalar(
            select(WorkoutPlan)
            .where(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == user_id)
            .options(
                selectinload(WorkoutPlan.days)
                .selectinload(WorkoutPlanDay.exercises)
                .joinedload(WorkoutPlanExercise.exercise)
            )
            .execution_options(populate_existing=True)
        )

    async def get_active_exercise(self, exercise_id: UUID) -> Exercise | None:
        return await self.session.scalar(
            select(Exercise).where(Exercise.id == exercise_id, Exercise.is_active.is_(True))
        )

    def add(self, value: object) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def delete(self, value: object) -> None:
        await self.session.delete(value)
