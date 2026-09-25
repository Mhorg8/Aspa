from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.modules.exercises.models import Exercise, ExerciseDifficulty
from app.modules.users.models import User

pytestmark = pytest.mark.integration


@dataclass
class PlanContext:
    user: User
    other_user: User
    headers: dict[str, str]
    other_headers: dict[str, str]
    bench_press_id: UUID
    row_id: UUID
    inactive_exercise_id: UUID


@pytest.fixture
async def plan_context(db_session: AsyncSession) -> PlanContext:
    user = User(phone_number="+989121111111", is_active=True)
    other_user = User(phone_number="+989122222222", is_active=True)
    bench_press = Exercise(
        name_fa="پرس سینه",
        name_en="Bench Press",
        difficulty=ExerciseDifficulty.INTERMEDIATE,
        is_active=True,
    )
    row = Exercise(
        name_fa="زیربغل قایقی",
        name_en="Seated Row",
        difficulty=ExerciseDifficulty.BEGINNER,
        is_active=True,
    )
    inactive = Exercise(
        name_fa="حرکت غیرفعال",
        name_en="Inactive Exercise",
        difficulty=ExerciseDifficulty.BEGINNER,
        is_active=False,
    )
    db_session.add_all([user, other_user, bench_press, row, inactive])
    await db_session.flush()
    return PlanContext(
        user=user,
        other_user=other_user,
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
        other_headers={"Authorization": f"Bearer {create_access_token(other_user.id)}"},
        bench_press_id=bench_press.id,
        row_id=row.id,
        inactive_exercise_id=inactive.id,
    )


async def _create_plan(client: AsyncClient, context: PlanContext) -> dict[str, object]:
    response = await client.post(
        "/api/workout-plans",
        headers=context.headers,
        json={"name": "Push Pull", "description": "Two day plan"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _add_day(
    client: AsyncClient, context: PlanContext, plan_id: str, name: str = "Push Day"
) -> dict[str, object]:
    response = await client.post(
        f"/api/workout-plans/{plan_id}/days",
        headers=context.headers,
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _add_exercise(
    client: AsyncClient,
    context: PlanContext,
    plan_id: str,
    day_id: str,
    exercise_id: UUID,
) -> dict[str, object]:
    response = await client.post(
        f"/api/workout-plans/{plan_id}/days/{day_id}/exercises",
        headers=context.headers,
        json={
            "exercise_id": str(exercise_id),
            "sets": 4,
            "min_reps": 8,
            "max_reps": 12,
            "rest_seconds": 120,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_complete_workout_plan_flow(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    plan = await _create_plan(integration_client, plan_context)
    plan_id = str(plan["id"])
    plan = await _add_day(integration_client, plan_context, plan_id)
    day = plan["days"][0]
    plan = await _add_exercise(
        integration_client,
        plan_context,
        plan_id,
        str(day["id"]),
        plan_context.bench_press_id,
    )

    item = plan["days"][0]["exercises"][0]
    assert item["exercise"]["name_en"] == "Bench Press"
    assert item["sets"] == 4
    assert item["min_reps"] == 8
    assert item["max_reps"] == 12
    assert item["rest_seconds"] == 120

    fetched = await integration_client.get(
        f"/api/workout-plans/{plan_id}", headers=plan_context.headers
    )
    listed = await integration_client.get("/api/workout-plans", headers=plan_context.headers)
    assert fetched.status_code == 200
    assert [value["id"] for value in listed.json()] == [plan_id]


async def test_exercises_can_be_edited_and_reordered(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    plan = await _create_plan(integration_client, plan_context)
    plan_id = str(plan["id"])
    plan = await _add_day(integration_client, plan_context, plan_id)
    day_id = str(plan["days"][0]["id"])
    plan = await _add_exercise(
        integration_client, plan_context, plan_id, day_id, plan_context.bench_press_id
    )
    plan = await _add_exercise(
        integration_client, plan_context, plan_id, day_id, plan_context.row_id
    )
    first, second = plan["days"][0]["exercises"]

    reordered = await integration_client.put(
        f"/api/workout-plans/{plan_id}/days/{day_id}/exercises/order",
        headers=plan_context.headers,
        json={"exercise_ids": [second["id"], first["id"]]},
    )
    assert reordered.status_code == 200, reordered.text
    assert [item["exercise"]["name_en"] for item in reordered.json()["days"][0]["exercises"]] == [
        "Seated Row",
        "Bench Press",
    ]

    updated = await integration_client.patch(
        f"/api/workout-plans/{plan_id}/days/{day_id}/exercises/{first['id']}",
        headers=plan_context.headers,
        json={"sets": 5, "min_reps": 6, "max_reps": 8, "notes": "Heavy"},
    )
    assert updated.status_code == 200, updated.text
    changed = next(
        item for item in updated.json()["days"][0]["exercises"] if item["id"] == first["id"]
    )
    assert (changed["sets"], changed["min_reps"], changed["max_reps"]) == (5, 6, 8)
    assert changed["notes"] == "Heavy"


async def test_plan_duplication_copies_nested_configuration(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    source = await _create_plan(integration_client, plan_context)
    source_id = str(source["id"])
    source = await _add_day(integration_client, plan_context, source_id)
    day_id = str(source["days"][0]["id"])
    source = await _add_exercise(
        integration_client,
        plan_context,
        source_id,
        day_id,
        plan_context.bench_press_id,
    )

    duplicated = await integration_client.post(
        f"/api/workout-plans/{source_id}/duplicate", headers=plan_context.headers
    )
    assert duplicated.status_code == 201, duplicated.text
    copy = duplicated.json()
    assert copy["id"] != source_id
    assert copy["name"] == "Push Pull (Copy)"
    assert copy["days"][0]["id"] != source["days"][0]["id"]
    assert copy["days"][0]["exercises"][0]["sets"] == 4


async def test_training_days_and_exercises_support_crud(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    plan = await _create_plan(integration_client, plan_context)
    plan_id = str(plan["id"])
    plan = await _add_day(integration_client, plan_context, plan_id, "Push")
    push_id = str(plan["days"][0]["id"])
    second = await integration_client.post(
        f"/api/workout-plans/{plan_id}/days",
        headers=plan_context.headers,
        json={"name": "Pull", "position": 0},
    )
    assert second.status_code == 201, second.text
    pull_id = str(second.json()["days"][0]["id"])
    assert [day["name"] for day in second.json()["days"]] == ["Pull", "Push"]

    updated = await integration_client.patch(
        f"/api/workout-plans/{plan_id}/days/{push_id}",
        headers=plan_context.headers,
        json={"name": "Upper", "position": 0},
    )
    assert updated.status_code == 200, updated.text
    assert [day["name"] for day in updated.json()["days"]] == ["Upper", "Pull"]

    with_exercise = await _add_exercise(
        integration_client,
        plan_context,
        plan_id,
        push_id,
        plan_context.bench_press_id,
    )
    item_id = str(with_exercise["days"][0]["exercises"][0]["id"])
    removed = await integration_client.delete(
        f"/api/workout-plans/{plan_id}/days/{push_id}/exercises/{item_id}",
        headers=plan_context.headers,
    )
    assert removed.status_code == 204

    deleted_day = await integration_client.delete(
        f"/api/workout-plans/{plan_id}/days/{pull_id}", headers=plan_context.headers
    )
    fetched = await integration_client.get(
        f"/api/workout-plans/{plan_id}", headers=plan_context.headers
    )
    assert deleted_day.status_code == 204
    assert len(fetched.json()["days"]) == 1
    assert fetched.json()["days"][0]["name"] == "Upper"
    assert fetched.json()["days"][0]["position"] == 0
    assert fetched.json()["days"][0]["exercises"] == []


async def test_archiving_filter_and_permanent_delete(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    plan = await _create_plan(integration_client, plan_context)
    plan_id = str(plan["id"])
    archived = await integration_client.patch(
        f"/api/workout-plans/{plan_id}",
        headers=plan_context.headers,
        json={"is_archived": True},
    )
    assert archived.status_code == 200

    active = await integration_client.get("/api/workout-plans", headers=plan_context.headers)
    all_plans = await integration_client.get(
        "/api/workout-plans",
        headers=plan_context.headers,
        params={"include_archived": True},
    )
    assert active.json() == []
    assert [item["id"] for item in all_plans.json()] == [plan_id]

    deleted = await integration_client.delete(
        f"/api/workout-plans/{plan_id}", headers=plan_context.headers
    )
    missing = await integration_client.get(
        f"/api/workout-plans/{plan_id}", headers=plan_context.headers
    )
    assert deleted.status_code == 204
    assert missing.status_code == 404


async def test_plan_ownership_is_enforced(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    plan = await _create_plan(integration_client, plan_context)
    plan_id = str(plan["id"])

    read = await integration_client.get(
        f"/api/workout-plans/{plan_id}", headers=plan_context.other_headers
    )
    update = await integration_client.patch(
        f"/api/workout-plans/{plan_id}",
        headers=plan_context.other_headers,
        json={"name": "Stolen"},
    )
    delete = await integration_client.delete(
        f"/api/workout-plans/{plan_id}", headers=plan_context.other_headers
    )
    assert read.status_code == update.status_code == delete.status_code == 404


async def test_invalid_exercise_and_configuration_are_rejected(
    integration_client: AsyncClient, plan_context: PlanContext
) -> None:
    plan = await _create_plan(integration_client, plan_context)
    plan_id = str(plan["id"])
    plan = await _add_day(integration_client, plan_context, plan_id)
    day_id = str(plan["days"][0]["id"])

    invalid_reps = await integration_client.post(
        f"/api/workout-plans/{plan_id}/days/{day_id}/exercises",
        headers=plan_context.headers,
        json={
            "exercise_id": str(plan_context.bench_press_id),
            "sets": 3,
            "min_reps": 12,
            "max_reps": 8,
        },
    )
    inactive = await integration_client.post(
        f"/api/workout-plans/{plan_id}/days/{day_id}/exercises",
        headers=plan_context.headers,
        json={
            "exercise_id": str(plan_context.inactive_exercise_id),
            "sets": 3,
            "min_reps": 8,
            "max_reps": 10,
        },
    )
    missing = await integration_client.post(
        f"/api/workout-plans/{plan_id}/days/{day_id}/exercises",
        headers=plan_context.headers,
        json={"exercise_id": str(uuid4()), "sets": 3, "min_reps": 8, "max_reps": 10},
    )
    assert invalid_reps.status_code == 422
    assert inactive.status_code == missing.status_code == 404


async def test_workout_plans_require_authentication(integration_client: AsyncClient) -> None:
    response = await integration_client.get("/api/workout-plans")
    assert response.status_code == 401
