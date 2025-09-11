from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    The default fields like email, name, date_joined are already included.
    """
    avatar_url = models.URLField(blank=True, null=True, verbose_name="Avatar URL")

    # Override the email field to be unique and required
    email = models.EmailField(unique=True, blank=False, null=False)

    # The 'name' field in the spec can be mapped to first_name/last_name or a new field.
    # For simplicity, we'll rely on first_name and last_name from AbstractUser.
    # The 'id' and 'date_joined' fields are automatically provided by Django.

    def __str__(self):
        return self.username
