from rest_framework import serializers
from .models import (Ingredient, Recipe, RecipeIngredient, Tag, ShoppingCart)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    author = serializers.StringRelatedField(read_only=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'image', 'description', 'ingredients', 'cooking_time', 'author', 'tags']


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(child=serializers.DictField(), write_only=True)
    tags = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Recipe
        fields = ['title', 'image', 'description', 'ingredients', 'cooking_time', 'tags']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

        recipe.tags.set(tags_data)
        return recipe
    
    def validate_ingredients(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один ингредиент.")
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError("Время приготовления должно быть не меньше 1 минуты.")
        return value


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ['id', 'recipe']
