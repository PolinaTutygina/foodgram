from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    Ingredient, Recipe, Subscription,
    RecipeIngredient, FavoriteRecipe, ShoppingCart,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_display',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count',
    )
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'email', 'avatar')
        }),
        ('Права доступа', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ('groups', 'user_permissions')
    ordering = ('username',)

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_display(self, user):
        if user.avatar:
            return (f'<img src="{user.avatar.url}" alt="Avatar" '
                     'style="width: 50px; height: 50px; border-radius: 50%;">')
        return 'Нет аватара'

    @admin.display(description='Рецепты')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписки')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def subscribers_count(self, user):
        return user.followers.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'user__email',
                     'author__username', 'author__email')
    list_filter = ('user', 'author')


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
