from rest_framework import viewsets, status
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.filters import SearchFilter
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from recipes.models import (
    Ingredient, Recipe, FavoriteRecipe, ShoppingCart, User, Subscription
)
from .serializers import (
    IngredientSerializer, RecipeSerializer, AuthorSubscriptionSerializer,
    RecipeCreateUpdateSerializer, AvatarSerializer, UserSerializer
)
from .filters import RecipeFilter
from .pagination import LimitPagination


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
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def add_to_favorites(self, request, id):
        return self.add_recipe_to_collection(
            request, id, FavoriteRecipe, 'избранное'
        )

    @add_to_favorites.mapping.delete
    def remove_from_favorites(self, request, id):
        get_object_or_404(
            FavoriteRecipe, user=request.user, recipe_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def add_to_shopping_cart(self, request, id):
        return self.add_recipe_to_collection(
            request, id, ShoppingCart, 'список покупок'
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, id):
        get_object_or_404(
            ShoppingCart, user=request.user, recipe_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_list(self, request):
        shopping_cart = request.user.shopping_cart.all()
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

    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticatedOrReadOnly])
    def get_short_link(self, request, id):
        get_object_or_404(Recipe, pk=id)
        short_link = request.build_absolute_uri(reverse(
            'recipe_redirect', kwargs={'recipe_id': id}
        ))
        return Response({"short_link": short_link}, status=status.HTTP_200_OK)

    def add_recipe_to_collection(
            self, request, recipe_id, model, collection_name
        ):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        _, created = model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            return Response(
                {'detail': f'Рецепт уже находится в {collection_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': f'Рецепт добавлен в {collection_name}.'},
            status=status.HTTP_201_CREATED
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
            request.user, data=request.data, partial=True
        )
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
        subscriptions = request.user.subscriptions.all()
        serializer = AuthorSubscriptionSerializer(
            subscriptions, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            AuthorSubscriptionSerializer(
                subscription, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated], url_path='unsubscribe')
    def unsubscribe(self, request, id):
        get_object_or_404(
            Subscription, user=request.user, author_id=id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
