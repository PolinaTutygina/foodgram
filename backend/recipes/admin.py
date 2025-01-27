from django.contrib import admin
from django.utils.safestring import mark_safe
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
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'cooking_time', 'author', 
        'favorite_count', 'display_ingredients', 'display_image'
    )
    search_fields = ('title', 'author__username', 'author__email')
    list_filter = ('cooking_time', 'author')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('favorite_count',)

    @admin.display(description='Ингредиенты')
    @mark_safe
    def display_ingredients(self, recipe):
    ingredients = recipe.ingredients.all()
    return (
        '<ul>' + ''.join(
            f'<li>{ingredient.name} ({ingredient.measurement_unit})</li>'
            for ingredient in ingredients
        ) + '</ul>'
    ) if ingredients else 'Нет ингредиентов'

    @admin.display(description='Картинка')
    @mark_safe
    def display_image(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" width="100" height="100" '
                'style="object-fit: cover; border-radius: 8px;">'
            )
        return 'Нет изображения'

    @admin.display(description='В избранном')
    def favorite_count(self, recipe):
        return recipe.favorite_set.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__title', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(FavoriteRecipe, ShoppingCart)
class FavoriteAndShoppingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__title')
    list_filter = ('user', 'recipe')
