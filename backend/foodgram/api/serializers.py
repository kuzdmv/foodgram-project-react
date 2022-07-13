import base64

from django.core.exceptions import ValidationError
from rest_framework import serializers
from djoser.serializers import UserSerializer
from recipes.models import (
    User, Tag, Ingredient, Recipes,
    IngredientRecipe, Favorite, ListToBuy, Subscript
)
from django.core.files.base import ContentFile


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'password'
        )

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        if self.context['request'].user.is_authenticated:
            return Subscript.objects.filter(
                author=obj, user=self.context['request'].user
            ).exists()
        return False

    def validate_username(self, value):
        if value == 'me':
            raise ValidationError(
                'Невозможно использовать зарезвированное имя "me".')
        return value


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_internal_value(self, data):
        id = data['id']
        if not Ingredient.objects.filter(id=id).exists():
            raise ValidationError(f'Нет такого ингридиента id={id}')
        if 'amount' not in data:
            raise ValidationError(f'Укажите кол-во для ингридиента id={id}')
        if int(data['amount']) <= 0:
            raise ValidationError(
                f'Укажите кол-во для ингридиента id={id} больше 0'
            )
        return data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipesSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(
        read_only=True,
        many=True
    )
    ingredients = IngredientRecipeSerializer(
        source='ingredientrecipe',
        many=True,
        read_only=True
    )
    text = serializers.CharField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id', 'name', 'author',
            'ingredients', 'tags', 'is_favorited', 'image',
            'is_in_shopping_cart', 'cooking_time', 'text'
        )

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_authenticated:
            return Favorite.objects.filter(
                recipe=obj, user=self.context['request'].user
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_authenticated:
            return ListToBuy.objects.filter(
                recipe=obj, user=self.context['request'].user
            ).exists()
        return False


class RecipesCreateSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True)
    tags = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngredientRecipeSerializer(
        source='ingredientrecipe',
        many=True
    )
    text = serializers.CharField(required=True)

    class Meta:
        model = Recipes
        fields = (
            'id', 'name', 'author', 'tags', 'image',
            'cooking_time', 'text', 'ingredients'
        )

    def to_internal_value(self, data):
        if 'image' not in data:
            return super(RecipesCreateSerializer, self).to_internal_value(data)
        imgstr = data.get('image')
        format, imgstr = imgstr.split(';base64,')
        ext = format.split('/')[-1]
        image = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        data['image'] = image
        return super(RecipesCreateSerializer, self).to_internal_value(data)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        if not tags:
            raise serializers.ValidationError('Укажите Теги')
        ingredientrecipe = validated_data.pop('ingredientrecipe')
        if not ingredientrecipe:
            raise serializers.ValidationError('Укажите Ингридиенты')
        receip = Recipes.objects.create(**validated_data)
        receip.tags.set(tags)
        for i in ingredientrecipe:
            IngredientRecipe.objects.create(
                recipe=receip,
                ingredient=Ingredient.objects.get(id=i['id']),
                amount=i['amount']
            )
        return receip

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredientrecipe = validated_data.pop('ingredientrecipe')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        for i in ingredientrecipe:
            IngredientRecipe.objects.create(
                recipe=instance,
                ingredient=Ingredient.objects.get(id=i['id']),
                amount=i['amount']
            )
        return super().update(instance, validated_data)

    def to_representation(self, value):
        return RecipesSerializer(
            value, context=self.context
        ).to_representation(value)


class RecipesSubscriptSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'recipes', 'recipes_count', 'is_subscribed'
        )

    def get_recipes(self, obj):
        queryset = Recipes.objects.filter(author=obj)
        if 'recipes_limit' in self.context:
            recipes_limit = int(self.context['recipes_limit'])
            queryset = Recipes.objects.filter(author=obj)[:recipes_limit]
        return RecipesSubscriptSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj).count()


class SubscriptCreateSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        if data['author'] == data['user']:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data

    def create(self, validated_data):
        if Subscript.objects.filter(**validated_data).exists():
            raise serializers.ValidationError('Нельзя подписаться дважды')
        Subscript.objects.create(**validated_data)
        return validated_data

    def to_representation(self, instance):
        return SubscriptSerializer(
            instance['author'], context=self.context
        ).to_representation(instance['author'])


class FavoriteRecipesCreateSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        return data

    def create(self, validated_data):
        if Favorite.objects.filter(**validated_data).exists():
            raise serializers.ValidationError('Рецепт уже в избранном')
        Favorite.objects.create(**validated_data)
        return validated_data

    def to_representation(self, instance):
        return RecipesSubscriptSerializer(instance['recipe']).data


class ListToBuyRecipesCreateSerializer(serializers.BaseSerializer):

    def to_internal_value(self, data):
        return data

    def create(self, validated_data):
        if ListToBuy.objects.filter(**validated_data).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок')
        ListToBuy.objects.create(**validated_data)
        return validated_data

    def to_representation(self, instance):
        return RecipesSubscriptSerializer(instance['recipe']).data


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"})
    current_password = serializers.CharField(style={"input_type": "password"})

    def validate_current_password(self, value):
        is_password_valid = self.context["request"].user.check_password(value)
        if is_password_valid:
            return value
        else:
            raise serializers.ValidationError('Неверный пароль')
