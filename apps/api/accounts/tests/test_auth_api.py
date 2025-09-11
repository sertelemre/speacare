import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
def test_user_registration_and_login():
    """
    Tests the full user registration and login flow.
    """
    client = APIClient()

    # 1. Register a new user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123",
        "password2": "strongpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    register_url = "/api/auth/register/"
    response = client.post(register_url, register_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.count() == 1
    assert User.objects.get().username == "testuser"

    # 2. Obtain JWT token
    login_data = {
        "username": "testuser",
        "password": "strongpassword123"
    }
    login_url = "/api/auth/jwt/obtain/"
    response = client.post(login_url, login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    access_token = response.data["access"]

    # 3. Access a protected endpoint (/api/auth/me/)
    me_url = "/api/auth/me/"
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    response = client.get(me_url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == "testuser"
    assert response.data["email"] == "test@example.com"

@pytest.mark.django_db
def test_registration_password_mismatch():
    """
    Tests that registration fails if passwords do not match.
    """
    client = APIClient()
    register_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "password1",
        "password2": "password2", # Mismatch
        "first_name": "Test",
        "last_name": "User"
    }
    register_url = "/api/auth/register/"
    response = client.post(register_url, register_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.count() == 0
