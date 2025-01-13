from django.urls import path
from .views import RegisterView, UserListView, CustomTokenObtainPairView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]