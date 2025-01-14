import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User
from recipes.serializers import RecipeSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']

    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")
        return value


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.subscribers.filter(id=request.user.id).exists()

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.avatar = validated_data.get('avatar', instance.avatar)

        instance.save()
        return instance


username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9@.+-_]+$',
    message="Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_"
)


class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    username = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=150,
        validators=[username_validator]
    )
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=150)
    last_name = serializers.CharField(required=True, allow_blank=False, max_length=150)
    password = serializers.CharField(write_only=True, required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        for field, value in attrs.items():
            if isinstance(value, str) and value.strip() == "":
                raise serializers.ValidationError({field: "Это поле не может быть пустым."})
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже используется.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Этот username уже используется.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class PasswordResetSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен быть не менее 8 символов.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'avatar', 'recipes', 'recipes_count'
        ]

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeSerializer(recipes, many=True).data


class SubscribeActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id']

    def validate_id(self, value):
        user = self.context['request'].user
        if value == user.id:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        if user.subscriptions.filter(id=value).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        target_user = User.objects.get(id=self.validated_data['id'])
        user.subscriptions.add(target_user)
        return target_user
