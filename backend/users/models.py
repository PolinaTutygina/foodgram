from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings


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


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
