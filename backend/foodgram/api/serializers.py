import base64

from django.core.exceptions import ValidationError
from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.core.files.base import ContentFile

from recipes.models import (
    User, Tag, Ingredient, Recipes,
    IngredientRecipe, Favorite, ListToBuy, Subscript
)


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
        if value.lower() == 'me':
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


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


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
    ingredients = IngredientRecipeCreateSerializer(many=True)
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

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Укажите Теги')
        return value

    def validate_ingredients(self, value):
        ingr_list = []
        for data in value:
            ingr_id = data['id'].pk
            if not data:
                raise serializers.ValidationError('Укажите Ингредиенты')
            if id in ingr_list:
                raise serializers.ValidationError(
                    'Нельзя указывать 2 одинаковых ингредиента'
                )
            ingr_list.append(id)
            if int(data['amount']) <= 0:
                raise serializers.ValidationError(
                    f'Укажите кол-во для ингредиента id={ingr_id} больше 0'
                )
        return value

    def create_ingredients(self, recipe, ingredients):
        objs = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(objs)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
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


class SubscriptCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscript
        fields = '__all__'

    def validate(self, value):
        method = self.context["request"].method
        author_list = value['user'].follower.values_list('author', flat=True)
        if method == 'POST':
            if value['user'] == value['author']:
                raise serializers.ValidationError('На себя подписаться нельзя')
            if value['author'].pk in author_list:
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого автора'
                )
        elif method == 'DELETE' and value['author'].pk not in author_list:
            raise serializers.ValidationError('Вы не подписаны на это автора')
        return value

    def to_representation(self, instance):
        return SubscriptSerializer(
            instance.author, context=self.context
        ).to_representation(instance.author)


class FavoriteRecipesCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'

    def validate(self, value):
        method = self.context["request"].method
        recipe_list = value['user'].favorite.values_list('recipe', flat=True)
        if method == 'POST' and value['recipe'].pk in recipe_list:
            raise serializers.ValidationError('Рецепт уже в избранном')
        elif method == 'DELETE' and value['recipe'].pk not in recipe_list:
            raise serializers.ValidationError('Рецепта нет в избранном')
        return value

    def to_representation(self, instance):
        return RecipesSubscriptSerializer(instance.recipe).data


class ListToBuyRecipesCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ListToBuy
        fields = '__all__'

    def validate(self, value):
        method = self.context["request"].method
        recipe_list = value['user'].listtobuy.values_list('recipe', flat=True)
        if method == 'POST' and value['recipe'].pk in recipe_list:
            raise serializers.ValidationError('Рецепт уже в списке')
        elif method == 'DELETE' and value['recipe'].pk not in recipe_list:
            raise serializers.ValidationError('Рецепта нет в списке')
        return value

    def to_representation(self, instance):
        return RecipesSubscriptSerializer(instance.recipe).data


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"})
    current_password = serializers.CharField(style={"input_type": "password"})

    def validate_current_password(self, value):
        is_password_valid = self.context["request"].user.check_password(value)
        if is_password_valid:
            return value
        else:
            raise serializers.ValidationError('Неверный пароль')
