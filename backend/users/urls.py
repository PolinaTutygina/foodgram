from django.urls import path
from .views import (
    UserViewSet, UserDetailView,
    CurrentUserView, AvatarUpdateView, PasswordResetView,
    SubscribeView, SubscriptionListView
)


urlpatterns = [
    path('', UserViewSet.as_view(), name='users'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('me/avatar/', AvatarUpdateView.as_view(), name='update_avatar'),
    path('set_password/', PasswordResetView.as_view(), name='set_password'),
    path('subscriptions/', SubscriptionListView.as_view(), name='subscriptions'),
    path('<int:id>/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]