from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.relations import PrimaryKeyRelatedField
from djoser.serializers import UserCreateSerializer, UserSerializer

from user.models import User
from user.functions import is_authenticated, Base64ImageField
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    Recipe_Ingredients,
    Cart,
    Favorite,
    Subscribe
)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для модели создания пользователя."""

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            User.USERNAME_FIELD,
            'password'
        )


class CustomUserSerializer(UserSerializer):
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
        request = self.context.get('request')
        if is_authenticated(request):
            return Subscribe.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


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


class Recipe_IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели связывающей модели репецтов и ингридиентов."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Recipe_Ingredients
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


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Подписки."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

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

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if is_authenticated(request):
            return obj.subscribing.filter(user=request.user).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit_recipes = request.query_params.get('recipes_limit')
        if limit_recipes is not None:
            recipes = obj.recipes.all()[:(int(limit_recipes))]
        else:
            recipes = obj.recipes.all()
        context = {'request': request}
        return RecipeShortSerializer(recipes, many=True,
                                     context=context).data


class SubcribeSerializer(serializers.Serializer):
    """Сериализатор для модели Подписки."""

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance, context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscribe.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise serializers.ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def create(self, validated_data):
        user = self.context.get('request').user
        author = get_object_or_404(User, pk=validated_data['id'])
        Subscribe.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author, context={'request': self.context.get('request')}
        )
        return serializer.data


class IngredientInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для представления ингридиентов в RecipeRead."""

    id = serializers.IntegerField(source='ingredients.id', read_only=True)
    name = serializers.CharField(source='ingredients.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit',
        read_only=True
    )

    class Meta:
        model = Recipe_Ingredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe на просмотр записей."""

    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    ingredients = IngredientInfoSerializer(
        many=True,
        read_only=True,
        source='recipeingredient'
    )
    author = CustomUserSerializer(read_only=True)
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
        request = self.context.get('request')
        if is_authenticated(request):
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if is_authenticated(request):
            return Cart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe на созднаии записей."""

    image = Base64ImageField(required=True)
    ingredients = Recipe_IngredientWriteSerializer(
        many=True,
        source='recipeingredient'
    )
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients_list = []
        ingredients = data.get('recipeingredient')
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент'
            )
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            if amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0'
                )
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиент с id={ingredient_id} не существует',
                    code=status.HTTP_400_BAD_REQUEST
                )
            ingredients_list.append(ingredient.id)
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                'Вы пытаетесь добавить в рецепт два одинаковых ингредиента'
            )
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег',
                code=status.HTTP_400_BAD_REQUEST
            )
        tag_ids = [tag.id for tag in tags]
        if len(set(tag_ids)) != len(tag_ids):
            raise serializers.ValidationError(
                'Повторяющиеся теги запрещены',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient,
                id=ingredient.get('id')
            )
            amount = ingredient.get('amount')
            ingredient_list.append(
                Recipe_Ingredients(
                    recipe=recipe,
                    ingredients=current_ingredient,
                    amount=amount
                )
            )
        Recipe_Ingredients.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredient')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipeingredient')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        Recipe_Ingredients.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(
            ingredients,
            instance
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'context': request}
        return RecipeReadSerializer(instance, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        if user.Favourites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = Cart
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        if user.carts.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в корзину'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
