from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet,
    IngredientListView,
    ShoppingCartView,
    FavoriteRecipeView,
    ShoppingCartListView,
    ShoppingListDownloadView,
    IngredientDetailView,
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('ingredients/', IngredientListView.as_view(), name='ingredient_list'),
    path('ingredients/<int:pk>/', IngredientDetailView.as_view(), name='ingredient_detail'),
    path('recipes/<int:recipe_id>/favorite/', FavoriteRecipeView.as_view(), name='favorite_recipe'),
    path('recipes/<int:recipe_id>/cart/', ShoppingCartView.as_view(), name='add_to_cart'),
    path('shopping_cart/', ShoppingCartListView.as_view(), name='shopping_cart'),
    path('shopping_list/download/', ShoppingListDownloadView.as_view(), name='download_shopping_list'),
]

urlpatterns += router.urls
