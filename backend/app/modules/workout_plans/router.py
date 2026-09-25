from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.modules.auth.dependencies import CurrentUser
from app.modules.workout_plans.dependencies import WorkoutPlanServiceDep
from app.modules.workout_plans.schemas import (
    ExerciseOrderUpdate,
    WorkoutPlanCreate,
    WorkoutPlanDayCreate,
    WorkoutPlanDayUpdate,
    WorkoutPlanExerciseCreate,
    WorkoutPlanExerciseUpdate,
    WorkoutPlanResponse,
    WorkoutPlanUpdate,
)

router = APIRouter(prefix="/workout-plans", tags=["workout plans"])


@router.get("", response_model=list[WorkoutPlanResponse])
async def list_plans(
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
    include_archived: Annotated[bool, Query()] = False,
) -> list[WorkoutPlanResponse]:
    return await service.list_plans(current_user.id, include_archived)


@router.post("", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: WorkoutPlanCreate, current_user: CurrentUser, service: WorkoutPlanServiceDep
) -> WorkoutPlanResponse:
    return await service.create_plan(current_user.id, data)


@router.get("/{plan_id}", response_model=WorkoutPlanResponse)
async def get_plan(
    plan_id: UUID, current_user: CurrentUser, service: WorkoutPlanServiceDep
) -> WorkoutPlanResponse:
    return await service.get_plan(plan_id, current_user.id)


@router.patch("/{plan_id}", response_model=WorkoutPlanResponse)
async def update_plan(
    plan_id: UUID,
    data: WorkoutPlanUpdate,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> WorkoutPlanResponse:
    return await service.update_plan(plan_id, current_user.id, data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID, current_user: CurrentUser, service: WorkoutPlanServiceDep
) -> Response:
    await service.delete_plan(plan_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{plan_id}/duplicate",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_plan(
    plan_id: UUID, current_user: CurrentUser, service: WorkoutPlanServiceDep
) -> WorkoutPlanResponse:
    return await service.duplicate_plan(plan_id, current_user.id)


@router.post(
    "/{plan_id}/days",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_day(
    plan_id: UUID,
    data: WorkoutPlanDayCreate,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> WorkoutPlanResponse:
    return await service.create_day(plan_id, current_user.id, data)


@router.patch("/{plan_id}/days/{day_id}", response_model=WorkoutPlanResponse)
async def update_day(
    plan_id: UUID,
    day_id: UUID,
    data: WorkoutPlanDayUpdate,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> WorkoutPlanResponse:
    return await service.update_day(plan_id, day_id, current_user.id, data)


@router.delete("/{plan_id}/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_day(
    plan_id: UUID,
    day_id: UUID,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> Response:
    await service.delete_day(plan_id, day_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{plan_id}/days/{day_id}/exercises",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_exercise(
    plan_id: UUID,
    day_id: UUID,
    data: WorkoutPlanExerciseCreate,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> WorkoutPlanResponse:
    return await service.add_exercise(plan_id, day_id, current_user.id, data)


@router.put(
    "/{plan_id}/days/{day_id}/exercises/order",
    response_model=WorkoutPlanResponse,
)
async def reorder_exercises(
    plan_id: UUID,
    day_id: UUID,
    data: ExerciseOrderUpdate,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> WorkoutPlanResponse:
    return await service.reorder_exercises(plan_id, day_id, current_user.id, data)


@router.patch(
    "/{plan_id}/days/{day_id}/exercises/{item_id}",
    response_model=WorkoutPlanResponse,
)
async def update_exercise(
    plan_id: UUID,
    day_id: UUID,
    item_id: UUID,
    data: WorkoutPlanExerciseUpdate,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> WorkoutPlanResponse:
    return await service.update_exercise(plan_id, day_id, item_id, current_user.id, data)


@router.delete(
    "/{plan_id}/days/{day_id}/exercises/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_exercise(
    plan_id: UUID,
    day_id: UUID,
    item_id: UUID,
    current_user: CurrentUser,
    service: WorkoutPlanServiceDep,
) -> Response:
    await service.remove_exercise(plan_id, day_id, item_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
