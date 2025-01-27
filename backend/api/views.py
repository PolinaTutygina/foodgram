from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.permissions import (IsAuthenticatedOrReadOnly)
from rest_framework.filters import SearchFilter
from django.http import HttpResponse
from io import BytesIO
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (Ingredient, Recipe, FavoriteRecipe, ShoppingCart,
                            User, Subscription)
from .serializers import (
    IngredientSerializer, RecipeSerializer, UserSerializer,
    UpdateRecipeSerializer, AvatarSerializer, AuthorSubscriptionSerializer
)
from .filters import RecipeFilter
from .pagination import LimitPagination

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UpdateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def add_to_favorites(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        if FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже находится в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FavoriteRecipe.objects.create(user=request.user, recipe=recipe)
        return Response(
            {'detail': 'Рецепт добавлен в избранное.'},
            status=status.HTTP_201_CREATED
        )

    @add_to_favorites.mapping.delete
    def remove_from_favorites(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        favorite = FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe).first()
        if not favorite:
            return Response(
                {'detail': 'Рецепт отсутствует в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def add_to_shopping_cart(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        if ShoppingCart.objects.filter(
            user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже находится в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        return Response(
            {'detail': 'Рецепт добавлен в список покупок.'},
            status=status.HTTP_201_CREATED
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        cart_item = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe).first()
        if not cart_item:
            return Response(
                {'detail': 'Рецепт отсутствует в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def list_shopping_cart(self, request):
        cart_items = ShoppingCart.objects.filter(user=request.user)
        recipes = [cart_item.recipe for cart_item in cart_items]
        serialized_data = RecipeSerializer(
            recipes, many=True, context={'request': request}).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_list(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        if not shopping_cart.exists():
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shopping_list = 'Список покупок:\n\n'
        for item in shopping_cart:
            recipe = item.recipe
            shopping_list += (
                f'- {recipe.name} (время приготовления: '
                f'{recipe.cooking_time} мин.)\n'
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


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
        paginator = LimitPagination()
        
        paginated_subscriptions = paginator.paginate_queryset(
            subscriptions, request
        )
        serializer = AuthorSubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request}
        )
        
        return paginator.get_paginated_response(serializer.data)

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
            AuthorSubscriptionSerializer(subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated], url_path='unsubscribe')
    def unsubscribe(self, request, id):
        get_object_or_404(
            Subscription, user=request.user, author_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
