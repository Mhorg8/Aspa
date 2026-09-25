from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.modules.exercises.dependencies import ExerciseServiceDep
from app.modules.exercises.models import ExerciseDifficulty
from app.modules.exercises.schemas import (
    CatalogReference,
    ExercisePage,
    ExerciseResponse,
    ExerciseSort,
    SortDirection,
)

router = APIRouter(tags=["exercises"])


@router.get("/exercises", response_model=ExercisePage)
async def list_exercises(
    service: ExerciseServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    muscle_group_id: UUID | None = None,
    equipment_id: UUID | None = None,
    difficulty: ExerciseDifficulty | None = None,
    sort: ExerciseSort = ExerciseSort.NAME_FA,
    direction: SortDirection = SortDirection.ASC,
) -> ExercisePage:
    return await service.list_exercises(
        page=page,
        page_size=page_size,
        search=search,
        muscle_group_id=muscle_group_id,
        equipment_id=equipment_id,
        difficulty=difficulty,
        sort=sort,
        direction=direction,
    )


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: UUID, service: ExerciseServiceDep) -> ExerciseResponse:
    return await service.get_exercise(exercise_id)


@router.get("/muscle-groups", response_model=list[CatalogReference])
async def list_muscle_groups(service: ExerciseServiceDep) -> list[CatalogReference]:
    return await service.list_muscle_groups()


@router.get("/equipment", response_model=list[CatalogReference])
async def list_equipment(service: ExerciseServiceDep) -> list[CatalogReference]:
    return await service.list_equipment()
