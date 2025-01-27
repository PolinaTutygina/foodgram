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
        return (f'<img src="{user.avatar.url}" alt="Avatar" '
                'style="width: 50px; height: 50px; border-radius: 50%;">'
                if user.avatar else '')

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
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_category'

    def lookups(self, request, model_admin):
        cooking_times = list(
            Recipe.objects.values_list('cooking_time', flat=True)
        )
        if not cooking_times:
            return []

        cooking_times.sort()
        one_third = len(cooking_times) // 3
        self.lower_bound = (cooking_times[one_third] 
                            if one_third > 0 
                            else min(cooking_times, default=10))

        self.upper_bound = (cooking_times[2 * one_third] 
                            if 2 * one_third > one_third 
                            else max(cooking_times, default=30))

        fast_count = Recipe.objects.filter(
            cooking_time__lt=self.lower_bound
        ).count()
        medium_count = Recipe.objects.filter(
            cooking_time__range=(self.lower_bound, self.upper_bound)
        ).count()
        long_count = Recipe.objects.filter(
            cooking_time__gt=self.upper_bound
        ).count()

        return [
            ('fast', f'Быстрее {self.lower_bound} мин ({fast_count})'),
            ('medium', (f'От {self.lower_bound} до {self.upper_bound} '
                        'мин ({medium_count})')),
            ('long', f'Дольше {self.upper_bound} мин ({long_count})'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lt=self.lower_bound)
        elif self.value() == 'medium':
            return queryset.filter(
                cooking_time__range=(self.lower_bound, self.upper_bound)
            )
        elif self.value() == 'long':
            return queryset.filter(cooking_time__gt=self.upper_bound)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author', 
        'favorite_count', 'display_ingredients', 'display_image'
    )
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = (CookingTimeFilter, 'author')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('favorite_count',)

    @admin.display(description='Ингредиенты')
    @mark_safe
    def display_ingredients(self, recipe):
        return '<br>'.join(
        f'{recipe_ingredient.ingredient.name} — '
        f'{recipe_ingredient.amount} '
        f'{recipe_ingredient.ingredient.measurement_unit}'
        for recipe_ingredient in recipe.recipeingredient_set.all()
    )

    @admin.display(description='Картинка')
    @mark_safe
    def display_image(self, recipe):
        return (
            f'<img src="{recipe.image.url}" width="100" height="100" '
            'style="object-fit: cover; border-radius: 8px;">'
            if recipe.image else ''
        )

    @admin.display(description='В избранном')
    def favorite_count(self, recipe):
        return recipe.user_recipe_relations.filter(
            favoriterecipe__isnull=False
        ).count()


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
