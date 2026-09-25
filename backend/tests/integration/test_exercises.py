from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.exercises.models import (
    Equipment,
    Exercise,
    ExerciseDifficulty,
    ExerciseMuscle,
    MuscleGroup,
)

pytestmark = pytest.mark.integration


@dataclass
class CatalogIds:
    bench_press: UUID
    push_up: UUID
    inactive_squat: UUID
    chest: UUID
    triceps: UUID
    inactive_muscle: UUID
    barbell: UUID
    bodyweight: UUID
    inactive_equipment: UUID


@pytest.fixture
async def exercise_catalog(db_session: AsyncSession) -> CatalogIds:
    chest = MuscleGroup(name_fa="سینه", name_en="Chest", is_active=True)
    triceps = MuscleGroup(name_fa="پشت بازو", name_en="Triceps", is_active=True)
    inactive_muscle = MuscleGroup(name_fa="غیرفعال", name_en="Inactive muscle", is_active=False)
    barbell = Equipment(name_fa="هالتر", name_en="Barbell", is_active=True)
    bodyweight = Equipment(name_fa="وزن بدن", name_en="Bodyweight", is_active=True)
    inactive_equipment = Equipment(
        name_fa="وسیله غیرفعال", name_en="Inactive equipment", is_active=False
    )
    bench_press = Exercise(
        name_fa="پرس سینه هالتر",
        name_en="Barbell Bench Press",
        description_fa="حرکت پرس برای عضلات سینه",
        description_en="A pressing movement for the chest",
        equipment=barbell,
        difficulty=ExerciseDifficulty.INTERMEDIATE,
        image_key="exercises/bench.webp",
        video_key="exercises/bench.mp4",
        is_active=True,
    )
    push_up = Exercise(
        name_fa="شنا سوئدی",
        name_en="Push Up",
        equipment=bodyweight,
        difficulty=ExerciseDifficulty.BEGINNER,
        is_active=True,
    )
    incline_press = Exercise(
        name_fa="پرس بالا سینه",
        name_en="Incline Press",
        equipment=barbell,
        difficulty=ExerciseDifficulty.ADVANCED,
        is_active=True,
    )
    inactive_squat = Exercise(
        name_fa="اسکات غیرفعال",
        name_en="Inactive Squat",
        difficulty=ExerciseDifficulty.BEGINNER,
        is_active=False,
    )
    bench_press.muscle_links = [
        ExerciseMuscle(muscle_group=chest, is_primary=True),
        ExerciseMuscle(muscle_group=triceps, is_primary=False),
    ]
    push_up.muscle_links = [ExerciseMuscle(muscle_group=chest, is_primary=True)]
    incline_press.muscle_links = [ExerciseMuscle(muscle_group=chest, is_primary=True)]
    db_session.add_all(
        [
            inactive_muscle,
            inactive_equipment,
            bench_press,
            push_up,
            incline_press,
            inactive_squat,
        ]
    )
    await db_session.flush()
    return CatalogIds(
        bench_press=bench_press.id,
        push_up=push_up.id,
        inactive_squat=inactive_squat.id,
        chest=chest.id,
        triceps=triceps.id,
        inactive_muscle=inactive_muscle.id,
        barbell=barbell.id,
        bodyweight=bodyweight.id,
        inactive_equipment=inactive_equipment.id,
    )


async def test_exercise_pagination_and_sorting(
    integration_client: AsyncClient, exercise_catalog: CatalogIds
) -> None:
    first = await integration_client.get(
        "/api/exercises", params={"page_size": 2, "sort": "name_en", "direction": "asc"}
    )
    second = await integration_client.get(
        "/api/exercises",
        params={"page": 2, "page_size": 2, "sort": "name_en", "direction": "asc"},
    )

    assert first.status_code == 200, first.text
    assert first.json()["total"] == 3
    assert first.json()["pages"] == 2
    assert [item["name_en"] for item in first.json()["items"]] == [
        "Barbell Bench Press",
        "Incline Press",
    ]
    assert [item["name_en"] for item in second.json()["items"]] == ["Push Up"]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"search": "bench"}, ["Barbell Bench Press"]),
        ({"search": "شنا"}, ["Push Up"]),
        ({"difficulty": "advanced"}, ["Incline Press"]),
    ],
)
async def test_exercise_search_and_simple_filters(
    integration_client: AsyncClient,
    exercise_catalog: CatalogIds,
    params: dict[str, str],
    expected: list[str],
) -> None:
    response = await integration_client.get("/api/exercises", params=params)

    assert response.status_code == 200, response.text
    assert [item["name_en"] for item in response.json()["items"]] == expected


async def test_exercise_filters_can_be_combined(
    integration_client: AsyncClient, exercise_catalog: CatalogIds
) -> None:
    response = await integration_client.get(
        "/api/exercises",
        params={
            "muscle_group_id": str(exercise_catalog.chest),
            "equipment_id": str(exercise_catalog.barbell),
            "difficulty": "intermediate",
        },
    )

    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()["items"]] == [str(exercise_catalog.bench_press)]


async def test_exercise_detail_includes_relationships_and_media_keys(
    integration_client: AsyncClient, exercise_catalog: CatalogIds
) -> None:
    response = await integration_client.get(f"/api/exercises/{exercise_catalog.bench_press}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["equipment"]["name_en"] == "Barbell"
    assert [muscle["name_en"] for muscle in body["primary_muscles"]] == ["Chest"]
    assert [muscle["name_en"] for muscle in body["secondary_muscles"]] == ["Triceps"]
    assert body["image_key"] == "exercises/bench.webp"
    assert body["video_key"] == "exercises/bench.mp4"


async def test_inactive_and_unknown_exercises_are_not_exposed(
    integration_client: AsyncClient, exercise_catalog: CatalogIds
) -> None:
    inactive = await integration_client.get(f"/api/exercises/{exercise_catalog.inactive_squat}")
    missing = await integration_client.get(f"/api/exercises/{uuid4()}")
    malformed = await integration_client.get("/api/exercises/not-a-uuid")

    assert inactive.status_code == 404
    assert missing.status_code == 404
    assert malformed.status_code == 422
    assert inactive.json()["error"]["code"] == "not_found"


async def test_reference_lists_hide_inactive_records(
    integration_client: AsyncClient, exercise_catalog: CatalogIds
) -> None:
    muscles = await integration_client.get("/api/muscle-groups")
    equipment = await integration_client.get("/api/equipment")

    assert muscles.status_code == 200
    assert equipment.status_code == 200
    assert {item["name_en"] for item in muscles.json()} == {"Chest", "Triceps"}
    assert {item["name_en"] for item in equipment.json()} == {"Barbell", "Bodyweight"}


async def test_exercise_query_validation(
    integration_client: AsyncClient, exercise_catalog: CatalogIds
) -> None:
    too_large = await integration_client.get("/api/exercises", params={"page_size": 101})
    invalid_difficulty = await integration_client.get(
        "/api/exercises", params={"difficulty": "impossible"}
    )

    assert too_large.status_code == 422
    assert invalid_difficulty.status_code == 422
