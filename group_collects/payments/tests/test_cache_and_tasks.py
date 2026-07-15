import pytest
from unittest.mock import patch

from django.core.cache import cache
from payments.models import Collect

@pytest.mark.django_db
def test_collect_list_is_cached(api_client, collect):
    cache.clear()
    url = "/api/collects/"

    first = api_client.get(url)
    assert first.status_code == 200

    second = api_client.get(url)
    assert second.status_code == 200
    assert first.data == second.data

@pytest.mark.django_db
def test_collect_detail_is_cached(api_client, collect):
    cache.clear()
    url = f"/api/collects/{collect.id}/"

    first = api_client.get(url)
    assert first.status_code == 200

    second = api_client.get(url)
    assert second.status_code == 200
    assert first.data == second.data

@pytest.mark.django_db
def test_cache_invalidated_after_collect_create(authenticated_client):
    cache.clear()
    authenticated_client.get("/api/collects/")

    data = {
        "title": "New Cached Collect",
        "reason": "birthday",
        "description": "desc",
        "target_amount": "1000.00",
        "status": "active",
    }
    response = authenticated_client.post("/api/collects/", data, format="json")
    assert response.status_code == 201

    assert cache.get("collects:list") is None

@pytest.mark.django_db
def test_cache_invalidated_after_collect_update(authenticated_client, collect):
    cache.clear()
    authenticated_client.get(f"/api/collects/{collect.id}/")

    response = authenticated_client.put(
        f"/api/collects/{collect.id}/",
        {
            "title": "Updated Title",
            "reason": "birthday",
            "description": "Updated description",
            "target_amount": "1000.00",
            "status": "active",
        },
        format="json",
    )
    assert response.status_code == 200
    assert cache.get(collect.cache_detail_key()) is None

@pytest.mark.django_db
def test_cache_invalidated_after_payment_create(authenticated_client, collect):
    cache.clear()
    authenticated_client.get(f"/api/collects/{collect.id}/")
    authenticated_client.get(f"/api/collects/{collect.id}/payments/")

    response = authenticated_client.post(
        f"/api/collects/{collect.id}/payments/",
        {"amount": "50.00"},
        format="json",
    )
    assert response.status_code == 201

    assert cache.get(collect.cache_detail_key()) is None
    assert cache.get(collect.cache_payments_key()) is None

@pytest.mark.django_db
def test_collect_create_enqueues_email_task(authenticated_client):
    data = {
        "title": "Email Collect",
        "reason": "birthday",
        "description": "desc",
        "target_amount": "1000.00",
        "status": "active",
    }
    with patch("payments.tasks.send_collect_created_email.delay") as mocked_delay:
        response = authenticated_client.post("/api/collects/", data, format="json")
        assert response.status_code == 201
        assert mocked_delay.called

@pytest.mark.django_db
def test_payment_create_enqueues_email_task(authenticated_client, collect):
    url = f"/api/collects/{collect.id}/payments/"
    with patch("payments.tasks.send_payment_created_email.delay") as mocked_delay:
        response = authenticated_client.post(url, {"amount": "50.00"}, format="json")
        assert response.status_code == 201
        assert mocked_delay.called

@pytest.mark.django_db
def test_cache_invalidated_after_collect_delete(authenticated_client, collect):
    cache.clear()
    authenticated_client.get(f"/api/collects/{collect.id}/")

    response = authenticated_client.delete(f"/api/collects/{collect.id}/")
    assert response.status_code == 204

    assert cache.get(collect.cache_detail_key()) is None
    assert cache.get(Collect.cache_list_key()) is None
    assert cache.get(collect.cache_payments_key()) is None

@pytest.mark.django_db
def test_cache_invalidated_after_payment_delete(authenticated_client, collect, payment):
    cache.clear()
    authenticated_client.get(f"/api/collects/{collect.id}/")
    authenticated_client.get(f"/api/collects/{collect.id}/payments/")

    response = authenticated_client.delete(f"/api/payments/{payment.id}/")
    assert response.status_code == 204

    assert cache.get(collect.cache_detail_key()) is None
    assert cache.get(collect.cache_payments_key()) is None
    assert cache.get(Collect.cache_list_key()) is None