from rest_framework import serializers, status
from drf_extra_fields.fields import Base64ImageField
from rest_framework.relations import PrimaryKeyRelatedField

from recipes.constants import MAX_CONST_FOR_COOK, MIN_CONST_FOR_COOK
from user.models import User, Subscribe
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    RecipeIngredients,
    Cart,
    Favorite,
)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели кастомной модели User."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return (
            request and request.user.is_authenticated
            and obj.subscribing.filter(user=request.user).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели связывающей модели репецтов и ингридиентов."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_CONST_FOR_COOK,
        max_value=MAX_CONST_FOR_COOK,
        error_messages={
            'min_value': ('Введенное значение должно быть не меньше '
                          '{min_value}.'),
            'max_value': ('Введенное значение должно быть не больше '
                          '{max_value}.')
        }
    )

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'amount'
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для модели короткого представления рецепта."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для модели Подписки."""

    recipes_count = serializers.IntegerField(default=0)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context['request']
        limit_recipes = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit_recipes:
            try:
                recipes = recipes[:int(limit_recipes)]
            except ValueError:
                pass
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SubcribeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Подписки."""

    class Meta:
        model = Subscribe
        fields = (
            'user',
            'author'
        )

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author, context=self.context
        ).data

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user.subscriber.filter(author=author).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data


class IngredientInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для представления ингридиентов в RecipeRead."""

    id = serializers.IntegerField(source='ingredients.id', read_only=True)
    name = serializers.CharField(source='ingredients.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe на просмотр записей."""

    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    ingredients = IngredientInfoSerializer(
        many=True,
        read_only=True,
        source='recipeingredients'
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        return (
            request and request.user.is_authenticated
            and obj.favourites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return (
            request and request.user.is_authenticated
            and obj.carts.filter(user=request.user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe на создании записей."""

    image = Base64ImageField(
        required=True,
        allow_null=False,
        allow_empty_file=False,
    )
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
    )
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_CONST_FOR_COOK,
        max_value=MAX_CONST_FOR_COOK,
        error_messages={
            'min_value': ('Введенное значение должно быть не меньше '
                          '{min_value}.'),
            'max_value': ('Введенное значение должно быть не больше '
                          '{max_value}.')
        }
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингридиент для рецепта'
            })
        ingredient_ids = [ingredient.get('id') for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Повторяющиеся ингредиенты запрещены'
            })
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Рецепт должен содержать хотя бы один тег'
            },
                code=status.HTTP_400_BAD_REQUEST
            )
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError({
                'tags': 'Повторяющиеся теги запрещены'
            },
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        ingredients_data = [
            RecipeIngredients(
                recipe=recipe,
                ingredients=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        RecipeIngredients.objects.bulk_create(ingredients_data)

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        RecipeIngredients.objects.filter(recipe=instance).delete()
        self.create_ingredients(
            ingredients,
            instance
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранных рецептов и списка покупок."""

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        model_name = self.Meta.model
        if model_name.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {model_name._meta.verbose_name}.'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(FavoriteShoppingCartSerializer):
    """Сериализатор избранных рецептов."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = Cart
        fields = ('user', 'recipe',)
