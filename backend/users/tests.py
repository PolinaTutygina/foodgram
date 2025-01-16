from django.test import TestCase
from users.models import User, Subscription


class UserModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", password="pass1"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="pass2"
        )

    def test_user_creation(self):
        """Тест создания пользователя."""
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.user1.username, "user1")
        self.assertEqual(self.user2.username, "user2")

    def test_subscription(self):
        """Тест подписки между пользователями."""
        Subscription.objects.create(
            user=self.user1, author=self.user2
        )
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user1, author=self.user2
            ).exists()
        )


