from rest_framework import generics, views, status
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (Ingredient, Recipe, FavoriteRecipe, Tag, ShoppingCart)
from .serializers import (IngredientSerializer, RecipeSerializer,
                          CreateRecipeSerializer, TagSerializer,
                          ShoppingCartSerializer, )


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientListView(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeListView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tags', 'author']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
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
