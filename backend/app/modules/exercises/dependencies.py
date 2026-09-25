from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.exercises.repository import ExerciseRepository
from app.modules.exercises.service import ExerciseService


async def get_exercise_service(session: DbSession) -> ExerciseService:
    return ExerciseService(ExerciseRepository(session))


ExerciseServiceDep = Annotated[ExerciseService, Depends(get_exercise_service)]
