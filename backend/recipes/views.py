from rest_framework import generics, views, status
from rest_framework.generics import RetrieveAPIView
from django.db.models import Sum
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (Ingredient, Recipe, FavoriteRecipe, Tag, ShoppingCart,
                     RecipeIngredient)
from .serializers import (IngredientSerializer, RecipeSerializer,
                          CreateRecipeSerializer, TagSerializer,
                          ShoppingCartSerializer, )


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientListView(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class IngredientDetailView(RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RecipeListView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tags', 'author']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRecipeSerializer
        return RecipeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=user)

        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            queryset = queryset.filter(in_cart__user=user)

        return queryset


class RecipeDetailView(RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class FavoriteRecipeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            FavoriteRecipe.objects.create(user=request.user, recipe=recipe)
            return Response({"detail": "Рецепт добавлен в избранное."}, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, recipe_id):
        try:
            favorite = FavoriteRecipe.objects.get(user=request.user, recipe_id=recipe_id)
            favorite.delete()
            return Response({"detail": "Рецепт удален из избранного."}, status=status.HTTP_204_NO_CONTENT)
        except FavoriteRecipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден в избранном."}, status=status.HTTP_404_NOT_FOUND)


class ShoppingCartView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response({"detail": "Рецепт добавлен в корзину."}, status=status.HTTP_201_CREATED)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({"detail": "Рецепт уже в корзине."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, recipe_id):
        try:
            cart_item = ShoppingCart.objects.get(user=request.user, recipe_id=recipe_id)
            cart_item.delete()
            return Response({"detail": "Рецепт удален из корзины."}, status=status.HTTP_204_NO_CONTENT)
        except ShoppingCart.DoesNotExist:
            return Response({"detail": "Рецепт не найден в корзине."}, status=status.HTTP_404_NOT_FOUND)


class ShoppingCartListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShoppingCartSerializer

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)


class ShoppingListDownloadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shopping_list = RecipeIngredient.objects.filter(
            recipe__in=request.user.shopping_cart.values_list('recipe', flat=True)
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        lines = [
            f"{item['ingredient__name']} ({item['ingredient__measurement_unit']}): {item['total_amount']}"
            for item in shopping_list
        ]
        response = Response(
            "\n".join(lines),
            content_type='text/plain',
            status=status.HTTP_200_OK
        )
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class RecipeShortLinkView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        short_link = f"{settings.SITE_DOMAIN}/recipes/{recipe_id}/"
        return Response({"short_link": short_link}, status=status.HTTP_200_OK)


class RecipeDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if recipe.author != request.user:
            return Response({"detail": "Вы не можете удалить чужой рецепт."}, status=status.HTTP_403_FORBIDDEN)
        recipe.delete()
        return Response({"detail": "Рецепт успешно удалён."}, status=status.HTTP_204_NO_CONTENT)
