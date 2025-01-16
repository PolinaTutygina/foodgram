from rest_framework import generics, views, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from io import BytesIO
from rest_framework.generics import ListAPIView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (Ingredient, Recipe, FavoriteRecipe, Tag, ShoppingCart)
from .serializers import (IngredientSerializer, RecipeSerializer,
                          CreateRecipeSerializer, TagSerializer,
                          ShoppingCartSerializer, )


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientListView(ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    http_method_names = ['get']

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class IngredientDetailView(RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RecipeListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        recipes = Recipe.objects.all()

        author = request.query_params.get('author')
        is_favorited = request.query_params.get('is_favorited')
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')
        search_name = request.query_params.get('search')

        if author:
            recipes = recipes.filter(author_id=author)
        if is_favorited:
            recipes = recipes.filter(favorite_recipes__user=request.user)
        if is_in_shopping_cart:
            recipes = recipes.filter(shopping_cart__user=request.user)
        if search_name:
            recipes = recipes.filter(name__icontains=search_name)

        paginator = PageNumberPagination()
        paginated_recipes = paginator.paginate_queryset(recipes, request)
        serializer = RecipeSerializer(paginated_recipes, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CreateRecipeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    def patch(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)

        if recipe.author != request.user:
            return Response(
                {"detail": "У вас недостаточно прав для выполнения действия."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateRecipeSerializer(
            recipe, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)

        if recipe.author != request.user:
            return Response(
                {'detail': 'У вас нет прав на изменение этого рецепта.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateRecipeSerializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)

        if recipe.author != request.user:
            return Response(
                {'detail': 'У вас нет прав на удаление этого рецепта.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteRecipeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        if FavoriteRecipe.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {"detail": "Рецепт уже находится в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FavoriteRecipe.objects.create(user=request.user, recipe=recipe)
        data = {
            "id": recipe.id,
            "name": recipe.name,
            "image": request.build_absolute_uri(recipe.image.url),
            "cooking_time": recipe.cooking_time,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        favorite = FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe).first()
        if not favorite:
            return Response(
                {"detail": "Рецепт отсутствует в избранном."},
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
                {"detail": "Рецепт уже находится в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        data = {
            "id": recipe.id,
            "name": recipe.name,
            "image": request.build_absolute_uri(recipe.image.url),
            "cooking_time": recipe.cooking_time,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        cart_item = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe).first()

        if not cart_item:
            return Response(
                {"detail": "Рецепт отсутствует в списке покупок."},
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
                {"detail": "Список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shopping_list = "Список покупок:\n\n"
        for item in shopping_cart:
            recipe = item.recipe
            shopping_list += (
                f"- {recipe.name} (время приготовления: "
                f"{recipe.cooking_time} мин.)\n"
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
        short_link = f"{settings.SITE_DOMAIN}/recipes/{recipe_id}/"
        return Response({"short_link": short_link}, status=status.HTTP_200_OK)


class RecipeDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if recipe.author != request.user:
            return Response(
                {"detail": "Вы не можете удалить чужой рецепт."},
                status=status.HTTP_403_FORBIDDEN
            )
        recipe.delete()
        return Response(
            {"detail": "Рецепт успешно удалён."},
            status=status.HTTP_204_NO_CONTENT
        )
