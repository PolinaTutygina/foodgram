from django.contrib import admin
from .models import (
    Ingredient, Recipe,
    RecipeIngredient, FavoriteRecipe, ShoppingCart,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'cooking_time',
                    'created_at', 'favorite_count')
    search_fields = ('title', 'author__username', 'author__email')
    list_filter = ('cooking_time', 'author')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('created_at', 'favorite_count')

    @admin.display(description='Количество добавлений в избранное')
    def favorite_count(self, obj):
        return obj.favorited_by.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__title', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__title')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__title')
    list_filter = ('user', 'recipe')
