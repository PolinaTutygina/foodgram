from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from .models import User, Subscription
from .serializers import (
    UserSerializer, AvatarSerializer, SubscriptionSerializer
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['put'],
            permission_classes=[IsAuthenticated], url_path='me/avatar')
    def update_avatar(self, request):
        if 'avatar' not in request.data:
            raise ValidationError({'avatar': 'Поле "avatar" обязательно.'})

        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'],
            permission_classes=[IsAuthenticated], url_path='me/avatar')
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated], url_path='me/subscriptions')
    def list_subscriptions(self, request):
        subscriptions = Subscription.objects.filter(user=request.user) 
        paginator = PageNumberPagination() 
        paginator.page_size = request.query_params.get('limit', 10) 
        paginated_subscriptions = paginator.paginate_queryset( 
            subscriptions, request
        ) 

        results = [ 
            SubscriptionSerializer(subscription, context={ 
                                   'request': request}).data 
            for subscription in paginated_subscriptions 
        ] 
        return paginator.get_paginated_response(results) 

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated], url_path='subscribe')
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)

        if author == request.user:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )

        if not created:
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            SubscriptionSerializer(subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated], url_path='unsubscribe')
    def unsubscribe(self, request, id):
        get_object_or_404(
            Subscription, user=request.user, author_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
