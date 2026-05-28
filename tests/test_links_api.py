import pytest

from paas_web_app.app import create_app


@pytest.fixture
def client():
    app = create_app(database_url="sqlite://", base_url="https://short.io")
    app.testing = True
    return app.test_client()


def test_links_crud_flow(client):
    # list empty
    response = client.get("/api/links")
    assert response.status_code == 200
    assert response.get_json() == []

    # create
    response = client.post(
        "/api/links",
        json={"original_url": "https://example.com/long-url", "short_name": "exmpl"},
    )
    assert response.status_code == 201
    created = response.get_json()
    assert created["id"] >= 1
    assert created["original_url"] == "https://example.com/long-url"
    assert created["short_name"] == "exmpl"
    assert created["short_url"] == "https://short.io/r/exmpl"

    link_id = created["id"]

    # list has one
    response = client.get("/api/links")
    assert response.status_code == 200
    assert response.get_json() == [created]

    # get by id
    response = client.get(f"/api/links/{link_id}")
    assert response.status_code == 200
    assert response.get_json() == created

    # update
    response = client.put(
        f"/api/links/{link_id}",
        json={"original_url": "https://example.com/long-url2", "short_name": "exmpl2"},
    )
    assert response.status_code == 200
    updated = response.get_json()
    assert updated["id"] == link_id
    assert updated["original_url"] == "https://example.com/long-url2"
    assert updated["short_name"] == "exmpl2"
    assert updated["short_url"] == "https://short.io/r/exmpl2"

    # delete
    response = client.delete(f"/api/links/{link_id}")
    assert response.status_code == 204
    assert response.data in (b"", None)

    # list empty again
    response = client.get("/api/links")
    assert response.status_code == 200
    assert response.get_json() == []


def test_links_duplicate_short_name_returns_same_error(client):
    response = client.post(
        "/api/links",
        json={"original_url": "https://example.com/1", "short_name": "dup"},
    )
    assert response.status_code == 201

    response = client.post(
        "/api/links",
        json={"original_url": "https://example.com/2", "short_name": "dup"},
    )
    assert response.status_code == 409
    assert response.get_json() == {"error": "short_name already exists"}


def test_links_404(client):
    response = client.get("/api/links/99999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found"}

    response = client.put(
        "/api/links/99999",
        json={"original_url": "https://example.com", "short_name": "x"},
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found"}

    response = client.delete("/api/links/99999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found"}

