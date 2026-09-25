from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.workout_plans.models import (
    WorkoutPlan,
    WorkoutPlanDay,
    WorkoutPlanExercise,
)
from app.modules.workout_plans.repository import WorkoutPlanRepository
from app.modules.workout_plans.schemas import (
    ExerciseOrderUpdate,
    PlanExerciseReference,
    WorkoutPlanCreate,
    WorkoutPlanDayCreate,
    WorkoutPlanDayResponse,
    WorkoutPlanDayUpdate,
    WorkoutPlanExerciseCreate,
    WorkoutPlanExerciseResponse,
    WorkoutPlanExerciseUpdate,
    WorkoutPlanResponse,
    WorkoutPlanUpdate,
)


class WorkoutPlanService:
    def __init__(self, session: AsyncSession, repository: WorkoutPlanRepository) -> None:
        self.session = session
        self.repository = repository

    @staticmethod
    def _response(plan: WorkoutPlan) -> WorkoutPlanResponse:
        return WorkoutPlanResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            is_archived=plan.is_archived,
            days=[
                WorkoutPlanDayResponse(
                    id=day.id,
                    name=day.name,
                    position=day.position,
                    exercises=[
                        WorkoutPlanExerciseResponse(
                            id=item.id,
                            exercise=PlanExerciseReference.model_validate(item.exercise),
                            position=item.position,
                            sets=item.sets,
                            min_reps=item.min_reps,
                            max_reps=item.max_reps,
                            rest_seconds=item.rest_seconds,
                            notes=item.notes,
                        )
                        for item in day.exercises
                    ],
                )
                for day in plan.days
            ],
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    async def _owned(self, plan_id: UUID, user_id: UUID) -> WorkoutPlan:
        plan = await self.repository.get_owned(plan_id, user_id)
        if plan is None:
            raise AppError("Workout plan not found", status_code=404, code="not_found")
        return plan

    @staticmethod
    def _day(plan: WorkoutPlan, day_id: UUID) -> WorkoutPlanDay:
        day = next((item for item in plan.days if item.id == day_id), None)
        if day is None:
            raise AppError("Workout plan day not found", status_code=404, code="not_found")
        return day

    @staticmethod
    def _plan_exercise(day: WorkoutPlanDay, item_id: UUID) -> WorkoutPlanExercise:
        item = next((value for value in day.exercises if value.id == item_id), None)
        if item is None:
            raise AppError("Workout plan exercise not found", status_code=404, code="not_found")
        return item

    async def _commit_and_get(self, plan_id: UUID, user_id: UUID) -> WorkoutPlanResponse:
        await self.session.commit()
        return self._response(await self._owned(plan_id, user_id))

    async def list_plans(self, user_id: UUID, include_archived: bool) -> list[WorkoutPlanResponse]:
        return [
            self._response(plan)
            for plan in await self.repository.list_owned(user_id, include_archived=include_archived)
        ]

    async def create_plan(self, user_id: UUID, data: WorkoutPlanCreate) -> WorkoutPlanResponse:
        plan = WorkoutPlan(
            user_id=user_id,
            name=data.name.strip(),
            description=data.description,
            is_archived=False,
        )
        self.repository.add(plan)
        await self.repository.flush()
        return await self._commit_and_get(plan.id, user_id)

    async def get_plan(self, plan_id: UUID, user_id: UUID) -> WorkoutPlanResponse:
        return self._response(await self._owned(plan_id, user_id))

    async def update_plan(
        self, plan_id: UUID, user_id: UUID, data: WorkoutPlanUpdate
    ) -> WorkoutPlanResponse:
        plan = await self._owned(plan_id, user_id)
        if data.name is not None:
            plan.name = data.name.strip()
        if "description" in data.model_fields_set:
            plan.description = data.description
        if data.is_archived is not None:
            plan.is_archived = data.is_archived
        return await self._commit_and_get(plan.id, user_id)

    async def delete_plan(self, plan_id: UUID, user_id: UUID) -> None:
        plan = await self._owned(plan_id, user_id)
        await self.repository.delete(plan)
        await self.session.commit()

    async def duplicate_plan(self, plan_id: UUID, user_id: UUID) -> WorkoutPlanResponse:
        source = await self._owned(plan_id, user_id)
        copy = WorkoutPlan(
            user_id=user_id,
            name=f"{source.name[:113]} (Copy)",
            description=source.description,
            is_archived=False,
        )
        for source_day in source.days:
            day = WorkoutPlanDay(name=source_day.name, position=source_day.position)
            day.exercises = [
                WorkoutPlanExercise(
                    exercise_id=item.exercise_id,
                    position=item.position,
                    sets=item.sets,
                    min_reps=item.min_reps,
                    max_reps=item.max_reps,
                    rest_seconds=item.rest_seconds,
                    notes=item.notes,
                )
                for item in source_day.exercises
            ]
            copy.days.append(day)
        self.repository.add(copy)
        await self.repository.flush()
        return await self._commit_and_get(copy.id, user_id)

    async def create_day(
        self, plan_id: UUID, user_id: UUID, data: WorkoutPlanDayCreate
    ) -> WorkoutPlanResponse:
        plan = await self._owned(plan_id, user_id)
        position = min(
            data.position if data.position is not None else len(plan.days), len(plan.days)
        )
        for day in plan.days:
            if day.position >= position:
                day.position += 1
        plan.days.append(WorkoutPlanDay(name=data.name.strip(), position=position))
        return await self._commit_and_get(plan.id, user_id)

    async def update_day(
        self, plan_id: UUID, day_id: UUID, user_id: UUID, data: WorkoutPlanDayUpdate
    ) -> WorkoutPlanResponse:
        plan = await self._owned(plan_id, user_id)
        day = self._day(plan, day_id)
        if data.name is not None:
            day.name = data.name.strip()
        if data.position is not None:
            ordered = [value for value in plan.days if value.id != day.id]
            ordered.insert(min(data.position, len(ordered)), day)
            for position, value in enumerate(ordered):
                value.position = position
        return await self._commit_and_get(plan.id, user_id)

    async def delete_day(self, plan_id: UUID, day_id: UUID, user_id: UUID) -> None:
        plan = await self._owned(plan_id, user_id)
        day = self._day(plan, day_id)
        await self.repository.delete(day)
        for position, value in enumerate(item for item in plan.days if item.id != day.id):
            value.position = position
        await self.session.commit()

    async def add_exercise(
        self,
        plan_id: UUID,
        day_id: UUID,
        user_id: UUID,
        data: WorkoutPlanExerciseCreate,
    ) -> WorkoutPlanResponse:
        plan = await self._owned(plan_id, user_id)
        day = self._day(plan, day_id)
        if await self.repository.get_active_exercise(data.exercise_id) is None:
            raise AppError("Exercise not found", status_code=404, code="not_found")
        position = min(
            data.position if data.position is not None else len(day.exercises),
            len(day.exercises),
        )
        for item in day.exercises:
            if item.position >= position:
                item.position += 1
        day.exercises.append(
            WorkoutPlanExercise(
                exercise_id=data.exercise_id,
                position=position,
                sets=data.sets,
                min_reps=data.min_reps,
                max_reps=data.max_reps,
                rest_seconds=data.rest_seconds,
                notes=data.notes,
            )
        )
        return await self._commit_and_get(plan.id, user_id)

    async def update_exercise(
        self,
        plan_id: UUID,
        day_id: UUID,
        item_id: UUID,
        user_id: UUID,
        data: WorkoutPlanExerciseUpdate,
    ) -> WorkoutPlanResponse:
        plan = await self._owned(plan_id, user_id)
        day = self._day(plan, day_id)
        item = self._plan_exercise(day, item_id)
        for field in ("sets", "rest_seconds"):
            if field in data.model_fields_set and getattr(data, field) is not None:
                setattr(item, field, getattr(data, field))
        if "notes" in data.model_fields_set:
            item.notes = data.notes
        min_reps = data.min_reps if data.min_reps is not None else item.min_reps
        max_reps = data.max_reps if data.max_reps is not None else item.max_reps
        if max_reps < min_reps:
            raise AppError("max_reps must be greater than or equal to min_reps")
        item.min_reps = min_reps
        item.max_reps = max_reps
        if data.position is not None:
            ordered = [value for value in day.exercises if value.id != item.id]
            ordered.insert(min(data.position, len(ordered)), item)
            for position, value in enumerate(ordered):
                value.position = position
        return await self._commit_and_get(plan.id, user_id)

    async def remove_exercise(
        self, plan_id: UUID, day_id: UUID, item_id: UUID, user_id: UUID
    ) -> None:
        plan = await self._owned(plan_id, user_id)
        day = self._day(plan, day_id)
        item = self._plan_exercise(day, item_id)
        await self.repository.delete(item)
        for position, value in enumerate(value for value in day.exercises if value.id != item.id):
            value.position = position
        await self.session.commit()

    async def reorder_exercises(
        self,
        plan_id: UUID,
        day_id: UUID,
        user_id: UUID,
        data: ExerciseOrderUpdate,
    ) -> WorkoutPlanResponse:
        plan = await self._owned(plan_id, user_id)
        day = self._day(plan, day_id)
        existing = {item.id: item for item in day.exercises}
        if set(data.exercise_ids) != set(existing):
            raise AppError("exercise_ids must contain every exercise in the day exactly once")
        for position, item_id in enumerate(data.exercise_ids):
            existing[item_id].position = position
        return await self._commit_and_get(plan.id, user_id)
