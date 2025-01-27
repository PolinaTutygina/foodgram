from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.filters import SearchFilter
from django.urls import reverse
from django.http import HttpResponse
from io import BytesIO
from django_filters.rest_framework import DjangoFilterBackend

from .models import Ingredient, Recipe, FavoriteRecipe, ShoppingCart
from .serializers import (
    IngredientSerializer, RecipeSerializer,
    CreateRecipeSerializer, ShoppingCartSerializer
)
from .filters import RecipeFilter
from users.pagination import LimitPagination


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
            return CreateRecipeSerializer
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

    @favorite.mapping.delete
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

    @cart.mapping.delete
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
        serializer = ShoppingCartSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

        buffer = BytesIO()
        buffer.write(shopping_list.encode('utf-8'))
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.pdf"'
        )
        return response

    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticatedOrReadOnly])
    def get_short_link(self, request, id):
        get_object_or_404(Recipe, pk=id)
        short_link = request.build_absolute_uri(reverse(
            'recipe_redirect',
            kwargs={'recipe_id': id}
        ))
        return Response({"short_link": short_link}, status=status.HTTP_200_OK)
