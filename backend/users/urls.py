from django.urls import path
from .views import (RegisterView, UserListView, CustomTokenObtainPairView,
                    AvatarUpdateView, PasswordResetView, UserDetailView,
                    CurrentUserView, SubscribeView, UnsubscribeView,
                    SubscriptionsListView,
                    )


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/me/avatar/', AvatarUpdateView.as_view(), name='update_avatar'),
    path('users/set_password/', PasswordResetView.as_view(), name='set_password'),
    path('users/me/', CurrentUserView.as_view(), name='current_user'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/subscriptions/', SubscriptionsListView.as_view(), name='subscriptions'),
    path('users/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('users/unsubscribe/<int:user_id>/', UnsubscribeView.as_view(), name='unsubscribe'),
]