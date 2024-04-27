from django.contrib import admin
from .models import (
    Tag,
    Recipe,
    Ingredient,
    Cart,
    Favorite,
    Subscribe,
    Recipe_Ingredients
)


class RecipeIngredientsInline(admin.TabularInline):
    model = Recipe_Ingredients


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
        'display_ingredients',
        'cooking_time',
        'text',
        'display_tags',
        'count_favorites',
        'pub_date',
    )
    search_fields = ('name', 'author')
    list_filter = ('author', 'tags')
    list_display_links = ('name',)
    inlines = [
        RecipeIngredientsInline
    ]

    @admin.display(description=' Ингредиенты ')
    def get_ingredients(self, obj):
        return '\n '.join([
            f'{item["ingredients__name"]} - {item["amount"]}'
            f' {item["ingredients__measurement_unit"]}.'
            for item in obj.recipeingredient_recipe.values(
                'ingredients__name',
                'amount', 'ingredients__measurement_unit')])

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return ', '.join([tag.name
                          for tag in obj.tags.all()])

    def count_favorites(self, obj):
        return obj.Favourites.count()


@admin.register(Recipe_Ingredients)
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
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_display_links = ('user',)
    empty_value_display = 'пусто'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')

    def save_model(self, request, obj, form, change):
        if obj.user == obj.author:
            self.message_user(
                request,
                "Нельзя подписаться на самого себя.",
                level='ERROR'
            )
            return
        super().save_model(request, obj, form, change)
