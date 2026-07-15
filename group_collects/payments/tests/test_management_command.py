import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from payments.models import Collect, Payment

@pytest.mark.django_db
def test_load_test_data_creates_users():
    call_command("load_test_data", "--users=3", "--collects=0", "--payments=0")
    assert User.objects.count() >= 3

@pytest.mark.django_db
def test_load_test_data_creates_collects():
    call_command("load_test_data", "--users=3", "--collects=5", "--payments=0")
    assert Collect.objects.count() >= 5

@pytest.mark.django_db
def test_load_test_data_creates_payments():
    call_command("load_test_data", "--users=3", "--collects=5", "--payments=10")
    assert Payment.objects.count() >= 10