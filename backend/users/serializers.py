from drf_extra_fields.fields import Base64ImageField
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User, Subscription
from recipes.models import Recipe
from djoser.serializers import UserSerializer as DjoserUserSerializer, UserCreateSerializer


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']

    def validate_avatar(self, avatar):
        if not avatar:
            raise serializers.ValidationError('Поле "avatar" обязательно.')
        return avatar


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + ['avatar']


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class AuthorSubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='author.recipes.count', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'recipes', 'recipes_count', 'avatar'
        ]

    def get_recipes(self, obj):
        limit = int(self.context['request'].query_params.get('recipes_limit', 10**10))
        recipes = obj.recipes.all()[:limit]
        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data
