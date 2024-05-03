from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Tag,
    Recipe,
    Ingredient,
    Cart,
    Favorite,
    RecipeIngredients
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 0
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админ панели для тегов."""

    list_filter = ('name', 'color', 'slug')
    list_display = ('pk', 'name', 'slug', 'color')
    search_fields = ('name', 'color', 'slug')
    list_display_links = ('name',)
    empty_value_display = 'пусто'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админ панели для ингридиентов."""

    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name',)
    list_display_links = ('name',)
    empty_value_display = 'пусто'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'cooking_time',
        'text',
        'display_tags',
        'display_ingredients',
        'count_favorites',
        'pub_date',
    )
    search_fields = ('name', 'author')
    list_filter = ('author', 'tags', 'name',)
    list_display_links = ('name',)
    inlines = (
        RecipeIngredientInline,
    )

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        return ', '.join([ingredient.ingredients.name
                          for ingredient in obj.recipeingredients.all()])

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return ', '.join([tag.name
                          for tag in obj.tags.all()])

    @admin.display(description='Количетсво избранных рецептов')
    def count_favorites(self, obj):
        return obj.favourites.count()

    @admin.display(description='Картинки')
    def show_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src={obj.image.url} width="80" height="60">'
            )


@admin.register(RecipeIngredients)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients', 'amount')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Настройка админ панели для корзины."""

    list_filter = ('user', 'recipe')
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = 'пусто'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админ панели для избранного."""

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_display_links = ('user',)
    empty_value_display = 'пусто'
