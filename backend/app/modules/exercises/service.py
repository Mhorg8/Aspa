from uuid import UUID

from app.core.exceptions import AppError
from app.modules.exercises.models import ExerciseDifficulty
from app.modules.exercises.repository import ExerciseRepository
from app.modules.exercises.schemas import (
    CatalogReference,
    ExercisePage,
    ExerciseResponse,
    ExerciseSort,
    SortDirection,
)


class ExerciseService:
    def __init__(self, repository: ExerciseRepository) -> None:
        self.repository = repository

    async def list_exercises(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        muscle_group_id: UUID | None,
        equipment_id: UUID | None,
        difficulty: ExerciseDifficulty | None,
        sort: ExerciseSort,
        direction: SortDirection,
    ) -> ExercisePage:
        normalized_search = search.strip() if search else None
        exercises, total = await self.repository.list_exercises(
            page=page,
            page_size=page_size,
            search=normalized_search or None,
            muscle_group_id=muscle_group_id,
            equipment_id=equipment_id,
            difficulty=difficulty.value if difficulty is not None else None,
            sort=sort,
            direction=direction,
        )
        return ExercisePage(
            items=[ExerciseResponse.from_model(exercise) for exercise in exercises],
            page=page,
            page_size=page_size,
            total=total,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_exercise(self, exercise_id: UUID) -> ExerciseResponse:
        exercise = await self.repository.get_active(exercise_id)
        if exercise is None:
            raise AppError("Exercise not found", status_code=404, code="not_found")
        return ExerciseResponse.from_model(exercise)

    async def list_muscle_groups(self) -> list[CatalogReference]:
        return [
            CatalogReference.model_validate(group)
            for group in await self.repository.list_muscle_groups()
        ]

    async def list_equipment(self) -> list[CatalogReference]:
        return [
            CatalogReference.model_validate(item) for item in await self.repository.list_equipment()
        ]
