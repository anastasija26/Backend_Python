import pytest
from decimal import Decimal

from payments.models import Payment


@pytest.mark.django_db
def test_payment_list_returns_200_and_expected_fields(api_client, collect, payment):
    response = api_client.get(f"/api/collects/{collect.id}/payments/")
    assert response.status_code == 200
    assert "results" in response.data
    item = response.data["results"][0]
    assert "id" in item
    assert "collect_id" in item
    assert "collect_title" in item
    assert "user" in item
    assert "amount" in item
    assert "created_at" in item


@pytest.mark.django_db
def test_payment_list_for_collect_returns_only_that_collect_payments(api_client, collect, donor, another_user):
    other_collect = collect.__class__.objects.create(
        author=another_user,
        title="Other Collect",
        reason="birthday",
        description="Other description",
        target_amount=Decimal("500.00"),
        status="active",
    )
    Payment.objects.create(
        collect=other_collect,
        user=donor,
        amount=Decimal("50.00"),
    )

    response = api_client.get(f"/api/collects/{collect.id}/payments/")
    assert response.status_code == 200
    for item in response.data["results"]:
        assert item["collect_id"] == collect.id


@pytest.mark.django_db
def test_payment_create_requires_auth(api_client, collect):
    url = f"/api/collects/{collect.id}/payments/"
    response = api_client.post(url, {"amount": "50.00"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_payment_create(authenticated_client, collect, user):
    url = f"/api/collects/{collect.id}/payments/"
    response = authenticated_client.post(url, {"amount": "50.00"}, format="json")
    assert response.status_code == 201

    payment = Payment.objects.get(id=response.data["id"])
    assert payment.collect_id == collect.id
    assert payment.user_id == user.id
    assert payment.amount == Decimal("50.00")


@pytest.mark.django_db
def test_payment_create_updates_collect_current_amount(authenticated_client, collect_with_payment):
    url = f"/api/collects/{collect_with_payment.id}/payments/"
    response = authenticated_client.post(url, {"amount": "50.00"}, format="json")
    assert response.status_code == 201

    collect_with_payment.refresh_from_db()
    assert collect_with_payment.current_amount == Decimal("150.00")


@pytest.mark.django_db
def test_payment_create_with_zero_amount_fails(authenticated_client, collect):
    url = f"/api/collects/{collect.id}/payments/"
    response = authenticated_client.post(url, {"amount": "0.00"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_payment_create_with_negative_amount_fails(authenticated_client, collect):
    url = f"/api/collects/{collect.id}/payments/"
    response = authenticated_client.post(url, {"amount": "-10.00"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_payment_retrieve(api_client, payment):
    response = api_client.get(f"/api/payments/{payment.id}/")
    assert response.status_code == 200
    assert response.data["id"] == payment.id
    assert response.data["amount"] == str(payment.amount)


@pytest.mark.django_db
def test_payment_detail_returns_expected_fields(api_client, payment):
    response = api_client.get(f"/api/payments/{payment.id}/")
    data = response.data
    assert "id" in data
    assert "collect_id" in data
    assert "collect_title" in data
    assert "user" in data
    assert "amount" in data
    assert "created_at" in data


@pytest.mark.django_db
def test_payment_update_requires_owner(authenticated_client_another, payment):
    response = authenticated_client_another.put(
        f"/api/payments/{payment.id}/",
        {"amount": "150.00"},
        format="json",
    )
    assert response.status_code in (403, 404)


@pytest.mark.django_db
def test_payment_update(authenticated_client, payment):
    response = authenticated_client.put(
        f"/api/payments/{payment.id}/",
        {"amount": "150.00"},
        format="json",
    )
    assert response.status_code == 200

    payment.refresh_from_db()
    assert payment.amount == Decimal("150.00")


@pytest.mark.django_db
def test_payment_update_recalculates_collect_current_amount(authenticated_client, payment):
    collect = payment.collect

    response = authenticated_client.put(
        f"/api/payments/{payment.id}/",
        {"amount": "150.00"},
        format="json",
    )
    assert response.status_code == 200

    collect.refresh_from_db()
    assert collect.current_amount == Decimal("150.00")


@pytest.mark.django_db
def test_payment_delete_requires_owner(authenticated_client_another, payment):
    response = authenticated_client_another.delete(f"/api/payments/{payment.id}/")
    assert response.status_code in (403, 404)


@pytest.mark.django_db
def test_payment_delete(authenticated_client, payment):
    response = authenticated_client.delete(f"/api/payments/{payment.id}/")
    assert response.status_code == 204
    assert not Payment.objects.filter(id=payment.id).exists()


@pytest.mark.django_db
def test_payment_delete_recalculates_collect_current_amount(authenticated_client, payment):
    collect = payment.collect

    response = authenticated_client.delete(f"/api/payments/{payment.id}/")
    assert response.status_code == 204

    collect.refresh_from_db()
    assert collect.current_amount == Decimal("0.00")