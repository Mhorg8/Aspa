from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.workout_plans.repository import WorkoutPlanRepository
from app.modules.workout_plans.service import WorkoutPlanService


async def get_workout_plan_service(session: DbSession) -> WorkoutPlanService:
    return WorkoutPlanService(session, WorkoutPlanRepository(session))


WorkoutPlanServiceDep = Annotated[WorkoutPlanService, Depends(get_workout_plan_service)]
