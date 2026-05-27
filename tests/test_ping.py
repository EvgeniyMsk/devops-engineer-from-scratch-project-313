import pytest

from main import app


@pytest.fixture
def client():
    return app.test_client()


def test_ping(client):
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'pong'
