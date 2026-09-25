from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.exercises.models import Exercise, ExerciseDifficulty


class ExerciseSort(StrEnum):
    NAME_FA = "name_fa"
    NAME_EN = "name_en"
    CREATED_AT = "created_at"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class CatalogReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_fa: str
    name_en: str


class ExerciseResponse(BaseModel):
    id: UUID
    name_fa: str
    name_en: str
    description_fa: str | None
    description_en: str | None
    equipment: CatalogReference | None
    difficulty: ExerciseDifficulty
    image_key: str | None
    video_key: str | None
    primary_muscles: list[CatalogReference]
    secondary_muscles: list[CatalogReference]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, exercise: Exercise) -> ExerciseResponse:
        primary = [
            CatalogReference.model_validate(link.muscle_group)
            for link in exercise.muscle_links
            if link.is_primary
        ]
        secondary = [
            CatalogReference.model_validate(link.muscle_group)
            for link in exercise.muscle_links
            if not link.is_primary
        ]
        return cls(
            id=exercise.id,
            name_fa=exercise.name_fa,
            name_en=exercise.name_en,
            description_fa=exercise.description_fa,
            description_en=exercise.description_en,
            equipment=(
                CatalogReference.model_validate(exercise.equipment)
                if exercise.equipment is not None
                else None
            ),
            difficulty=exercise.difficulty,
            image_key=exercise.image_key,
            video_key=exercise.video_key,
            primary_muscles=primary,
            secondary_muscles=secondary,
            created_at=exercise.created_at,
            updated_at=exercise.updated_at,
        )


class ExercisePage(BaseModel):
    items: list[ExerciseResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
