from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "name": "CodeScope",
        "version": "1.0.0",
    }


def test_analyze_repository(tmp_path):
    source_file = tmp_path / "main.py"
    source_file.write_text(
        "# FIXME: example\nprint('hello')\nprint('codescope')\n",
        encoding="utf-8",
    )

    response = client.post("/api/analyze", json={"path": str(tmp_path)})
    assert response.status_code == 200

    data = response.json()
    assert data["files"] == 1
    assert data["analyzed_files"] == 1
    assert data["lines"] == 3
    assert data["languages"] == {"Python": 1}
    assert data["todos"][0]["tag"] == "FIXME"
    assert data["hotspots"][0]["path"] == "main.py"


def test_repository_not_found():
    response = client.post(
        "/api/analyze",
        json={"path": "Z:/this-path-should-not-exist/codescope"},
    )
    assert response.status_code == 404


def test_empty_path_is_rejected():
    response = client.post("/api/analyze", json={"path": ""})
    assert response.status_code == 422
