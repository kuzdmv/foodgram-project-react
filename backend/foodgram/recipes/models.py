from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (USER, 'user'),
        (ADMIN, 'admin'),
    ]
    first_name = models.CharField('Имя', max_length=15)
    last_name = models.CharField('Фамилия', max_length=254)
    email = models.EmailField(max_length=254, unique=True)
    bio = models.TextField(
        'Информация о пользователе',
        help_text='Введите краткую информацию о себе',
        blank=True,
        null=True,
    )
    role = models.CharField(max_length=9, choices=ROLE_CHOICES, default=USER)
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        self.is_active = True
        if self.role == self.ADMIN:
            self.is_staff = True
        super(User, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField('Название', max_length=256, unique=True)
    color = models.CharField('Цвет', max_length=256, unique=True)
    slug = models.SlugField('slug', max_length=50, unique=True)

    class Meta:
        ordering = ('slug',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=256)
    measurement_unit = models.CharField('Единицы', max_length=20)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipes(models.Model):
    name = models.CharField('Название', max_length=256)
    text = models.TextField('Описание', null=True, blank=True)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes',
        blank=True,
        verbose_name='Тег',
    )
    ingredients = models.ManyToManyField(
        Ingredient, related_name='ingredients', through='IngredientRecipe'
    )
    cooking_time = models.PositiveIntegerField('Время приготовления')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredientrecipe'
    )
    recipe = models.ForeignKey(
        Recipes, on_delete=models.CASCADE,
        related_name='ingredientrecipe'
    )
    amount = models.PositiveIntegerField('Колличество')

    class Meta:
        verbose_name = 'Кол-во ингредиента для рецпта'
        verbose_name_plural = 'Кол-во ингредиента для рецпта'
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_ingr_recipes')
        ]

    def __str__(self):
        return f'{self.recipe} id - {self.recipe.pk}, {self.ingredient}'


class Subscript(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_sub_users')
        ]

    def __str__(self):
        return f'{self.user} id - {self.user.pk}, {self.author}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='favorite')

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_fav_recipes')
        ]

    def __str__(self):
        return f'{self.user} id - {self.user.pk}, {self.recipe}'


class ListToBuy(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listtobuy'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='listtobuy')

    class Meta:
        ordering = ('user',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списоки покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_buy_recipes')
        ]

    def __str__(self):
        return f'{self.user} id - {self.user.pk}, {self.recipe}'
