from django.core.validators import MinValueValidator
from django.db import models
from user.models import User

from .constants import (
    NAME_CONST_CHAR,
    SLUG_CONST_CHAR,
    MIN_CONST_FOR_COOK
)


class Name(models.Model):
    """Абстрактная модель, описывающая имена."""
    name = models.CharField(
        max_length=NAME_CONST_CHAR,
        verbose_name='Название',
    )

    class Meta:
        abstract = True
        ordering = ('name', )


class Tag(Name):
    """Модель описывающая теги."""
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        unique=True,
    )
    slug = models.SlugField(
        unique=True,
        max_length=SLUG_CONST_CHAR,
        verbose_name='Уникальный идентификатор',
    )

    class Meta(Name.Meta):
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(Name):
    """Модель описывающая игридиенты."""
    measurement_unit = models.CharField(
        max_length=NAME_CONST_CHAR,
        verbose_name='Единица измерения'
    )

    class Meta(Name.Meta):
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(Name):
    """Модель описывающая рецепты."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='Recipe_Ingredients',
        verbose_name='Ингридиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_CONST_FOR_COOK,
                message='Минимальное время приготовления составляет 1 мин.'
            )
        ],
        verbose_name='Время готовки в минутах'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta(Name.Meta):
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class Recipe_Ingredients(models.Model):
    """Вспомогательный класс для модели Recipe"""
    recipe = models.ForeignKey(
        verbose_name='В каких рецептах',
        to=Recipe,
        on_delete=models.CASCADE,
    )
    ingredients = models.ForeignKey(
        verbose_name='Связанные ингредиенты',
        to=Ingredient,
        on_delete=models.CASCADE,
        null=False
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Количество ингридиентов'
        default_related_name = 'recipeingredient'
        ordering = ('recipe',)

    def __str__(self):
        return (
            f'{self.ingredients.name} ({self.ingredients.measurement_unit}) - '
            f'{self.amount}'
        )


class UserRecipe(models.Model):
    """Абстрактный базовый класс для моделей Favorite и Cart."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)


class Favorite(UserRecipe):
    """Модель описывающая избранное."""

    class Meta(UserRecipe.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'Favourites'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_recipe_user'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class Cart(UserRecipe):
    """Модель описывающая корзину."""

    class Meta(UserRecipe.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'В корзине'
        default_related_name = 'carts'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Корзину покупок'


class Subscribe(models.Model):
    """Модель описывающая подписки."""
    user = models.ForeignKey(
        User,
        related_name='subscriber',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='subscribing',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_user_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
