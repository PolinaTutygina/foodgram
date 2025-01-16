from rest_framework.views import APIView
from rest_framework import views, generics, status, mixins
from .pagination import CustomPagination
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import User, Subscription
from .permissions import (IsGuest, IsAuthenticatedUser,
                          IsAuthenticatedOrReadOnly)
from .serializers import (
    UserSerializer, RegisterUserSerializer, AvatarSerializer,
    PasswordResetSerializer, SubscriptionSerializer
)


class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RegisterUserSerializer
        return UserSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsGuest()]
        return [IsAuthenticatedOrReadOnly()]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CurrentUserView(views.APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AvatarUpdateView(views.APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if 'avatar' not in request.data:
            raise ValidationError({"avatar": "Поле 'avatar' обязательно."})

        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetView(views.APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        serializer = PasswordResetSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Пароль успешно изменен."},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get("limit", 10)
        paginated_subscriptions = paginator.paginate_queryset(
            subscriptions, request)

        results = [
            SubscriptionSerializer(subscription, context={
                                   "request": request}).data
            for subscription in paginated_subscriptions
        ]
        return paginator.get_paginated_response(results)


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        author = get_object_or_404(User, pk=id)

        if author == request.user:
            return Response(
                {"detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Subscription.objects.filter(
            user=request.user, author=author
        ).exists():
            return Response(
                {"detail": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = Subscription.objects.create(
            user=request.user, author=author)
        return Response(
            SubscriptionSerializer(subscription, context={
                                   "request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, id):
        author = get_object_or_404(User, pk=id)
        subscription = Subscription.objects.filter(
            user=request.user, author=author).first()

        if not subscription:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
