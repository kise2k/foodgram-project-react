from django.contrib import admin

from .models import Tag, Recipe, Ingredient, Cart, Favorite, Subscribe


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админ панели для тегов."""
    list_filter = ('name', )
    list_display = ('name', 'slug', 'color')
    search_fields = ('name',)
    empty_value_display = 'пусто'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админ панели для ингридиентов."""
    list_filter = ('name', )
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = 'пусто'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админ панели для репецтов."""
    list_filter = ('name', 'author', 'tags')
    list_display = ('name', 'author', 'count_favorites', 'id')
    search_fields = ('name',)
    empty_value_display = 'пусто'

    def count_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Настройка админ панели для корзины."""
    list_filter = ('recipe', 'user')
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = 'пусто'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админ панели для избранного."""
    list_filter = ('recipe', 'user')
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = 'пусто'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )
