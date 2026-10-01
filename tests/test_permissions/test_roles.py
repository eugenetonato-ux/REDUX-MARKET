import pytest
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.accounts.roles import UserRole


@pytest.mark.django_db
def test_buyer_role_by_default():
    user = User.objects.create_user(email="buyer@redux.app", password="password123")
    assert user.role == UserRole.BUYER
    assert user.is_buyer is True
    assert user.is_admin is False


@pytest.mark.django_db
def test_cannot_self_assign_admin_in_regular_registration():
    with pytest.raises(ValidationError):
        User.objects.create_user(email="hacker@redux.app", password="password123", role=UserRole.ADMIN)


@pytest.mark.django_db
def test_create_superuser_assigns_admin():
    admin_user = User.objects.create_superuser(email="superadmin@redux.app", password="password123")
    assert admin_user.role == UserRole.ADMIN
    assert admin_user.is_admin is True
    assert admin_user.is_staff is True
