from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    subscriptions = models.ManyToManyField(
        'self', symmetrical=False, related_name='subscribers', blank=True
    )

    def __str__(self):
        return self.username
