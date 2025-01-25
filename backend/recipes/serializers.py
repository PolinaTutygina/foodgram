from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
from .utils import resolve_placeholders
from .models import (Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, FavoriteRecipe)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_author(self, obj):
        user = self.context.get('request').user
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'is_subscribed': obj.author.subscribers.filter(
                id=user.id
            ).exists() if user.is_authenticated else False,
        }

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'title', 'image', 'description', 'ingredients', 
            'cooking_time', 'created_at', 'is_favorited', 'is_in_shopping_cart'
        ]


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'image', 'title',
                  'description', 'cooking_time')
    
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def validate(self, data):
        data = resolve_placeholders(data)
        return super().validate(data)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.')
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть не меньше 1 минуты.')
        return value


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ['id', 'recipe']
