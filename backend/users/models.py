from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    subscriptions = models.ManyToManyField(
        'self', symmetrical=False, related_name='subscribers', blank=True
    )
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        blank=True
    )

    def __str__(self):
        return self.username
