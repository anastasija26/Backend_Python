import pytest
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from payments.models import Collect, Payment


@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="testpass123",
    )


@pytest.fixture
def another_user():
    return User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        first_name="Another",
        last_name="User",
        password="testpass123",
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def authenticated_client_another(api_client, another_user):
    api_client.force_authenticate(user=another_user)
    return api_client


@pytest.fixture
def author(user):
    return user


@pytest.fixture
def donor(user):
    return user


@pytest.fixture
def collect(author):
    return Collect.objects.create(
        author=author,
        title="Test Collect",
        reason="birthday",
        description="Test description",
        target_amount=Decimal("1000.00"),
        status="active",
    )


@pytest.fixture
def collect_with_payment(author, user):
    collect = Collect.objects.create(
        author=author,
        title="Test Collect With Payment",
        reason="birthday",
        description="Test description with payment",
        target_amount=Decimal("1000.00"),
        status="active",
    )
    Payment.objects.create(
        collect=collect,
        user=user,
        amount=Decimal("100.00"),
    )
    collect.refresh_from_db()
    return collect


@pytest.fixture
def payment(collect, donor):
    return Payment.objects.create(
        collect=collect,
        user=donor,
        amount=Decimal("100.00"),
    )