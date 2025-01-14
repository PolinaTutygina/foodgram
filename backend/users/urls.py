from django.urls import path, include
from .views import (
    UserViewSet, UserDetailView, 
    CurrentUserView, AvatarUpdateView, PasswordResetView, 
    SubscribeView, SubscriptionsListView
)


urlpatterns = [
    #path('', UserListView.as_view(), name='user_list'),
    #path('', RegisterUserView.as_view(), name='register_user'),
    path('', UserViewSet.as_view(), name='users'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('me/avatar/', AvatarUpdateView.as_view(), name='update_avatar'),
    path('set_password/', PasswordResetView.as_view(), name='set_password'),
    path('subscriptions/', SubscriptionsListView.as_view(), name='subscriptions'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
]