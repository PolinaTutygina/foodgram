from rest_framework import generics, views, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter
from .models import (Ingredient, Recipe, FavoriteRecipe, ShoppingCart)
from .serializers import (IngredientSerializer, RecipeSerializer,
                          CreateRecipeSerializer, ShoppingCartSerializer)


class IngredientListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        name = request.query_params.get('name', '')
        ingredients = Ingredient.objects.all()

        if name:
            ingredients = ingredients.filter(name__istartswith=name)

        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IngredientDetailView(RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RecipePagination(PageNumberPagination):
    page_size = 6


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteRecipeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        if FavoriteRecipe.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже находится в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FavoriteRecipe.objects.create(user=request.user, recipe=recipe)
        data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url),
            'cooking_time': recipe.cooking_time,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
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


class ShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)

        if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже находится в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url),
            'cooking_time': recipe.cooking_time,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
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


class ShoppingCartListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShoppingCartSerializer

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)


class ShoppingListDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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


class RecipeShortLinkView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id):
        get_object_or_404(Recipe, id=recipe_id)
        short_link = f'{settings.SITE_DOMAIN}/recipes/{recipe_id}/'
        return Response({"short_link": short_link}, status=status.HTTP_200_OK)


class RecipeDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if recipe.author != request.user:
            return Response(
                {'detail': 'Вы не можете удалить чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        recipe.delete()
        return Response(
            {'detail': 'Рецепт успешно удалён.'},
            status=status.HTTP_204_NO_CONTENT
        )
