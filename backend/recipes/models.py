from django.core.validators import MinValueValidator, MaxValueValidator
from colorfield.fields import ColorField
from django.db import models

from user.models import User
from .constants import (
    NAME_CONST_CHAR,
    SLUG_CONST_CHAR,
    MIN_CONST_FOR_COOK,
    MAX_CONST_FOR_COOK,
    SIZE_FOR_COLOR
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
    color = ColorField(
        verbose_name='Цвет',
        max_length=SIZE_FOR_COLOR,
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

    class Meta():
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit',),
                name='unique_name_measurement_unit'
            )
        ]
        ordering = ('name',)

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
        through='RecipeIngredients',
        verbose_name='Ингридиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                MIN_CONST_FOR_COOK,
                message=f'Минимальное значение {MIN_CONST_FOR_COOK}.'),
            MaxValueValidator(
                MAX_CONST_FOR_COOK,
                message=f'Максимальное значение {MAX_CONST_FOR_COOK}.')
        ),
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


class RecipeIngredients(models.Model):
    """Вспомогательный класс для модели Recipe"""
    recipe = models.ForeignKey(
        verbose_name='В каких рецептах',
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredients'
    )
    ingredients = models.ForeignKey(
        verbose_name='Связанные ингредиенты',
        to=Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        default=1,
        validators=(
            MinValueValidator(
                MIN_CONST_FOR_COOK,
                message=f'Мин. количество ингридиентов {MIN_CONST_FOR_COOK}'
            ),
            MaxValueValidator(
                MAX_CONST_FOR_COOK,
                message=f'Макс. количество ингридиентов {MAX_CONST_FOR_COOK}'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredients',),
                name='unique_recipe_ingredient'
            )
        ]

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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        unique_constraint_name = f'unique_{cls.__name__.lower()}_user_recipe'
        cls._meta.constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name=unique_constraint_name
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}"'\
               f' в {self._meta.verbose_name}'


class Favorite(UserRecipe):
    """Модель описывающая избранное."""

    class Meta(UserRecipe.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favourites'


class Cart(UserRecipe):
    """Модель описывающая корзину."""

    class Meta(UserRecipe.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'В корзине'
        default_related_name = 'carts'
