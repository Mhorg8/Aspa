from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PlanName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class WorkoutPlanCreate(BaseModel):
    name: PlanName
    description: str | None = Field(default=None, max_length=2000)


class WorkoutPlanUpdate(BaseModel):
    name: PlanName | None = None
    description: str | None = Field(default=None, max_length=2000)
    is_archived: bool | None = None


class WorkoutPlanDayCreate(BaseModel):
    name: PlanName
    position: int | None = Field(default=None, ge=0)


class WorkoutPlanDayUpdate(BaseModel):
    name: PlanName | None = None
    position: int | None = Field(default=None, ge=0)


class WorkoutPlanExerciseCreate(BaseModel):
    exercise_id: UUID
    sets: int = Field(ge=1, le=20)
    min_reps: int = Field(ge=1, le=100)
    max_reps: int = Field(ge=1, le=100)
    rest_seconds: int = Field(default=90, ge=0, le=3600)
    notes: str | None = Field(default=None, max_length=500)
    position: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_rep_range(self) -> WorkoutPlanExerciseCreate:
        if self.max_reps < self.min_reps:
            raise ValueError("max_reps must be greater than or equal to min_reps")
        return self


class WorkoutPlanExerciseUpdate(BaseModel):
    sets: int | None = Field(default=None, ge=1, le=20)
    min_reps: int | None = Field(default=None, ge=1, le=100)
    max_reps: int | None = Field(default=None, ge=1, le=100)
    rest_seconds: int | None = Field(default=None, ge=0, le=3600)
    notes: str | None = Field(default=None, max_length=500)
    position: int | None = Field(default=None, ge=0)


class ExerciseOrderUpdate(BaseModel):
    exercise_ids: list[UUID] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicates(self) -> ExerciseOrderUpdate:
        if len(self.exercise_ids) != len(set(self.exercise_ids)):
            raise ValueError("exercise_ids must not contain duplicates")
        return self


class PlanExerciseReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_fa: str
    name_en: str


class WorkoutPlanExerciseResponse(BaseModel):
    id: UUID
    exercise: PlanExerciseReference
    position: int
    sets: int
    min_reps: int
    max_reps: int
    rest_seconds: int
    notes: str | None


class WorkoutPlanDayResponse(BaseModel):
    id: UUID
    name: str
    position: int
    exercises: list[WorkoutPlanExerciseResponse]


class WorkoutPlanResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_archived: bool
    days: list[WorkoutPlanDayResponse]
    created_at: datetime
    updated_at: datetime
