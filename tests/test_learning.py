import os
import sys
import json
import pytest

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# Ensure project root is on path for imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import Maqam  # noqa: E402


@pytest.fixture(scope="function")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_minimal_data()
    yield app
    # cleanup DB file between tests
    with app.app_context():
        db.session.remove()
        try:
            db.engine.dispose()
        except Exception:
            pass
        db.drop_all()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass


def seed_minimal_data():
    m = Maqam(
        name_ar="سيكاه",
        name_en="Sika",
        emotion="sad",
        usage="Malouf",
        ajnas_json=json.dumps([]),
        regions_json=json.dumps(["tunis"]),
        description_en="",
        description_ar="",
        difficulty_index=0.2,
        difficulty_label="beginner",
        rarity_level="common",
    )
    db.session.add(m)
    db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


def auth_header(client):
    res = client.get("/auth/demo-token")
    assert res.status_code == 200
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_complete_activity_and_leaderboard(client):
    headers = auth_header(client)

    # log an activity
    res = client.post(
        "/learning/complete-activity",
        json={"maqam_id": 1, "activity": "mcq_emotion"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["progress"] == 1

    # leaderboard should reflect activities
    res = client.get("/learning/leaderboard")
    assert res.status_code == 200
    board = res.get_json()["leaderboard"]
    assert len(board) == 1
    assert board[0]["activities"] == 1
    assert board[0]["quizzes"] == 0


def test_activity_log_self_scope(client):
    headers = auth_header(client)

    # log two activities
    client.post("/learning/complete-activity", json={"maqam_id": 1, "activity": "a1"}, headers=headers)
    client.post("/learning/complete-activity", json={"maqam_id": 1, "activity": "a2"}, headers=headers)

    res = client.get("/learning/activity-log", headers=headers)
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["count"] == 2
    acts = payload["activities"]
    assert len(acts) == 2
    assert acts[0]["activity"] in {"a1", "a2"}


def test_leaderboard_updates_after_quiz(client):
    headers = auth_header(client)

    # Start quiz
    res = client.post("/learning/quiz/start", json={"lang": "en"}, headers=headers)
    assert res.status_code == 200
    quiz = res.get_json()
    answers = [None] * quiz["count"]  # intentionally blank answers

    res = client.post(f"/learning/quiz/{quiz['quiz_id']}/answer", json={"answers": answers}, headers=headers)
    assert res.status_code == 200

    # leaderboard now has quizzes counted
    res = client.get("/learning/leaderboard")
    board = res.get_json()["leaderboard"]
    assert len(board) == 1
    assert board[0]["quizzes"] == 1


def test_activity_log_forbidden_other_user(client):
    headers = auth_header(client)

    # log one activity as demo user
    client.post("/learning/complete-activity", json={"maqam_id": 1, "activity": "a1"}, headers=headers)

    # attempt to read another user's log should be forbidden for learners
    res = client.get("/learning/activity-log?user_id=someoneelse@example.com", headers=headers)
    assert res.status_code == 403


def test_knowledge_endpoints(client):
    # list maqamet
    res = client.get("/knowledge/maqam")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 1

    # fetch by name
    res = client.get("/knowledge/maqam/by-name/Sika")
    assert res.status_code == 200
    detail = res.get_json()
    assert detail.get("name", {}).get("en") == "Sika"


def test_analysis_and_recommendation(client):
    headers = auth_header(client)

    # analysis should return candidates
    res = client.post("/analysis/notes", json={"notes": ["C", "D", "E"], "optional_mood": "sad"}, headers=headers)
    assert res.status_code == 200
    cand = res.get_json().get("candidates", [])
    assert isinstance(cand, list)

    # recommendation should return 200 with recommendations list
    res = client.post(
        "/recommendations/maqam",
        json={"mood": "sad", "region": "tunis"},
        headers=headers,
    )
    assert res.status_code == 200
    recs = res.get_json().get("recommendations", [])
    assert isinstance(recs, list)


def test_flashcards_and_plan_require_auth(client):
    # flashcards are public
    res = client.get("/learning/flashcards")
    assert res.status_code == 200

    # plan requires auth
    res = client.get("/learning/plan")
    assert res.status_code == 401

    headers = auth_header(client)
    res = client.get("/learning/plan", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("count") >= 0


def test_matching_game_and_activity_log(client):
    headers = auth_header(client)
    res = client.get("/learning/matching?topic=emotion", headers=headers)
    assert res.status_code == 200
    payload = res.get_json()
    assert "left" in payload and "right" in payload

    # log one activity to ensure activity-log still works
    client.post("/learning/complete-activity", json={"maqam_id": 1, "activity": "matching_emotion"}, headers=headers)
    res = client.get("/learning/activity-log", headers=headers)
    assert res.status_code == 200
    assert res.get_json().get("count") >= 1


def test_contribution_submission(client):
    headers = auth_header(client)
    res = client.post(
        "/knowledge/maqam/1/contributions",
        json={"type": "anecdote", "payload": {"note": "Test"}},
        headers=headers,
    )
    assert res.status_code in (201, 200)
    body = res.get_json()
    assert "status" in body
