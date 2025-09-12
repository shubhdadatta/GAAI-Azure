from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_analyze_skills():
    req = {
        "current_role": "Business Analyst",
        "target_role": "Data Scientist",
        "skills": ["SQL", "Excel"],
        "desired_skills": ["Python", "Machine Learning"]
    }
    response = client.post("/analyze_skills", json=req)
    assert response.status_code == 200
    assert "analysis" in response.json()
