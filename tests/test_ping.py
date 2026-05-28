import pytest

from paas_web_app.app import create_app


@pytest.fixture
def client():
    app = create_app(database_url="sqlite://", base_url="https://short.io")
    return app.test_client()


def test_ping(client):
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'pong'
