from django.urls import path
from .views import (IngredientListView, RecipeListView, RecipeDetailView,
                    FavoriteRecipeView, TagListView, ShoppingCartView,
                    ShoppingCartListView, ShoppingListDownloadView)


urlpatterns = [
    path('ingredients/', IngredientListView.as_view(), name='ingredient_list'),
    path('recipes/', RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<int:pk>/', RecipeDetailView.as_view(), name='recipe_detail'),
    path('recipes/<int:recipe_id>/favorite/', FavoriteRecipeView.as_view(), name='favorite_recipe'),
    path('tags/', TagListView.as_view(), name='tag_list'),
    path('recipes/<int:recipe_id>/cart/', ShoppingCartView.as_view(), name='add_to_cart'),
    path('shopping_cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('shopping_list/download/', ShoppingListDownloadView.as_view(), name='download_shopping_list'),
]