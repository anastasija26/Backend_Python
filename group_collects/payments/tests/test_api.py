import pytest

@pytest.mark.django_db
def test_collect_list_view(api_client, collect):
    response = api_client.get("/api/collects/")
    assert response.status_code == 200
    assert "results" in response.data
    assert len(response.data["results"]) >= 1

@pytest.mark.django_db
def test_collect_list_returns_expected_fields(api_client, collect):
    response = api_client.get("/api/collects/")
    item = response.data["results"][0]
    assert "id" in item
    assert "author" in item
    assert "title" in item
    assert "reason" in item
    assert "current_amount" in item
    assert "status" in item
    assert "end_date" in item
    assert "created_at" in item

@pytest.mark.django_db
def test_collect_create_requires_auth(api_client):
    data = {
        "title": "Test Collect",
        "reason": "birthday",
        "description": "Test description",
        "target_amount": "1000.00",
        "status": "active",
    }
    response = api_client.post("/api/collects/", data, format="json")
    assert response.status_code == 401

@pytest.mark.django_db
def test_collect_create_view(authenticated_client):
    data = {
        "title": "Test Collect",
        "reason": "birthday",
        "description": "Test description",
        "target_amount": "1000.00",
        "status": "active",
    }
    response = authenticated_client.post("/api/collects/", data, format="json")
    assert response.status_code == 201
    assert response.data["title"] == "Test Collect"
    assert response.data["reason"] == "birthday"

@pytest.mark.django_db
def test_collect_create_sets_author_automatically(authenticated_client, user):
    data = {
        "title": "Author Collect",
        "reason": "birthday",
        "description": "Test description",
        "target_amount": "1000.00",
        "status": "active",
    }
    response = authenticated_client.post("/api/collects/", data, format="json")
    assert response.status_code == 201
    assert response.data["author"]["id"] == user.id

@pytest.mark.django_db
def test_collect_create_with_past_end_date_fails(authenticated_client):
    data = {
        "title": "Bad Collect",
        "reason": "birthday",
        "description": "Test description",
        "target_amount": "1000.00",
        "end_date": "2000-01-01T00:00:00Z",
        "status": "active",
    }
    response = authenticated_client.post("/api/collects/", data, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_collect_create_with_negative_target_amount_fails(authenticated_client):
    data = {
        "title": "Bad Collect",
        "reason": "birthday",
        "description": "Test description",
        "target_amount": "-10.00",
        "status": "active",
    }
    response = authenticated_client.post("/api/collects/", data, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_collect_detail_view(api_client, collect, payment):
    response = api_client.get(f"/api/collects/{collect.id}/")
    assert response.status_code == 200
    assert response.data["title"] == "Test Collect"
    assert "payments" in response.data

@pytest.mark.django_db
def test_collect_detail_returns_expected_fields(api_client, collect, payment):
    response = api_client.get(f"/api/collects/{collect.id}/")
    data = response.data
    assert "id" in data
    assert "author" in data
    assert "title" in data
    assert "reason" in data
    assert "description" in data
    assert "target_amount" in data
    assert "current_amount" in data
    assert "cover" in data
    assert "end_date" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "payments" in data

@pytest.mark.django_db
def test_collect_detail_payments_feed_has_amount_datetime_full_name(api_client, collect, payment):
    response = api_client.get(f"/api/collects/{collect.id}/")
    payments = response.data["payments"]
    assert len(payments) == 1
    item = payments[0]
    assert "amount" in item
    assert "created_at" in item
    assert "user" in item
    assert "full_name" in item["user"]

@pytest.mark.django_db
def test_collect_update_requires_owner(authenticated_client_another, collect):
    response = authenticated_client_another.put(
        f"/api/collects/{collect.id}/",
        {
            "title": "Hacked Title",
            "reason": "birthday",
            "description": "Hacked description",
            "target_amount": "2000.00",
            "status": "active",
        },
        format="json",
    )
    assert response.status_code in (403, 404)

@pytest.mark.django_db
def test_collect_delete_requires_owner(authenticated_client_another, collect):
    response = authenticated_client_another.delete(f"/api/collects/{collect.id}/")
    assert response.status_code in (403, 404)

@pytest.mark.django_db
def test_collect_update_by_owner_success(authenticated_client, collect):
    response = authenticated_client.put(
        f"/api/collects/{collect.id}/",
        {
            "title": "Updated Title",
            "reason": "wedding",
            "description": "Updated description",
            "target_amount": "1500.00",
            "status": "active",
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.data["title"] == "Updated Title"

@pytest.mark.django_db
def test_collect_delete_by_owner_success(authenticated_client, collect):
    response = authenticated_client.delete(f"/api/collects/{collect.id}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_collect_delete_by_owner_success(authenticated_client, collect):
    response = authenticated_client.delete(f"/api/collects/{collect.id}/")
    assert response.status_code == 204