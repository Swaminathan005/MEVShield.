from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "MEVShield Backend is running"}
    print("Root endpoint OK")

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] == True
    print("Health endpoint OK:", data)

def test_status_stopped():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "STOPPED"
    print("Status endpoint (stopped) OK:", data)

def test_start():
    response = client.post("/api/start")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RUNNING"
    print("Start endpoint OK:", data)

def test_transactions_before_advance():
    # After start, but before any advance, transactions endpoint should return empty list
    # because /api/transactions calls advance if RUNNING.
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    # Since the endpoint advances the stream, we expect at least one transaction if data available
    print("Transactions endpoint after start:", len(data), "items")
    if data:
        print("First transaction:", data[0])

def test_statistics():
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_scanned" in data
    print("Statistics endpoint OK:", data)

if __name__ == "__main__":
    test_root()
    test_health()
    test_status_stopped()
    test_start()
    test_transactions_before_advance()
    test_statistics()
    print("All tests passed!")