from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "name": "CodeScope",
        "version": "0.1.0",
    }


def test_analyze_repository(tmp_path):
    source_file = tmp_path / "main.py"

    source_file.write_text(
        "print('hello')\nprint('codescope')\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/analyze",
        json={
            "path": str(tmp_path),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["files"] == 1
    assert data["lines"] == 2
    assert data["languages"] == {
        "Python": 1,
    }


def test_repository_not_found():
    response = client.post(
        "/api/analyze",
        json={
            "path": "Z:/this-path-should-not-exist/codescope",
        },
    )

    assert response.status_code == 404