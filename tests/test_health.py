from fastapi.testclient import TestClient
from apps.api.app.main import app

def test_offline_health():
    assert TestClient(app).get('/api/health').json()['provider'] == 'mock'
