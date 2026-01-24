from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

from user.managers import UserManager


class User(AbstractUser):
    """
    Custom User model that uses email as the unique identifier
    instead of a username.
    """

    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.email
