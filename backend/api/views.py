from collections import defaultdict

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.db.models import Sum, Count, F
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from djoser.views import UserViewSet

from recipes.models import (
    Cart,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    Tag,
    User,
)
from user.models import Subscribe
from .filter import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permission import IsAuthorOrAdminOrReadOnly
from .serializers import (
    UserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubcribeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вывод ингридиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    """Вывод тегов."""

    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Вывод рецептов."""

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('tags', 'ingredients')
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def create_instance(serializer_class, recipe_id, request):
        """Статический метод для создания записи."""

        context = {'request': request}
        data = {'user': request.user.id, 'recipe': recipe_id}
        serializer = serializer_class(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def make_shopping_list(ingredients_queryset):
        """Функция для создания списка покупок."""

        ingredients_dict = defaultdict(int)

        for ingredient in ingredients_queryset:
            ingredients_dict[
                ingredient['ingredient_name']
            ] += ingredient['amount']

        shopping_list = ['Список покупок:\n']

        for counter, (name, amount) in enumerate(
            ingredients_dict.items(),
            start=1
        ):
            shopping_list.append(
                f'\n{counter}. {name} - '
                f'{amount} {ingredient["measurement_unit"]}'
            )

        return shopping_list

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Отправка файла со списком покупок."""

        ingredients_queryset = RecipeIngredients.objects.filter(
            recipe__carts__user=request.user
        ).values(
            ingredient_name=F('ingredients__name'),
            measurement_unit=F('ingredients__measurement_unit')
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient_name')

        shopping_list = self.make_shopping_list(ingredients_queryset)

        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавление рецепта в избранное."""

        return self.create_instance(
            FavoriteSerializer,
            pk,
            request
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаление рецепта из избранного."""

        favorite_obj_after_filter = Favorite.objects.filter(
            user=request.user,
            recipe_id=pk
        )
        if not favorite_obj_after_filter.exists():
            raise ValidationError('Рецепт не найден в избранном.')
        favorite_obj_after_filter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добавление рецепта в список покупок."""

        return self.create_instance(
            ShoppingCartSerializer,
            pk,
            request
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаление рецепта из списка покупок."""

        favorite_obj_after_filter = Cart.objects.filter(
            user=request.user,
            recipe_id=pk
        )
        if not favorite_obj_after_filter.exists():
            raise ValidationError('Рецепт не найден в списке покупок.')
        favorite_obj_after_filter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(UserViewSet):
    """Вывод пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ('me', 'subscribe', 'unsubscribe'):
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        serializer = SubcribeSerializer(
            data={'user': request.user.id, 'author': id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        subcription = Subscribe.objects.filter(
            user=request.user, author=id
        )
        if subcription.exists():
            subcription.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        users = User.objects.filter(subscribing__user=request.user).annotate(
            recipes_count=Count('recipes')
        )
        paginated_queryset = self.paginate_queryset(users)
        serializer = SubscriptionSerializer(
            paginated_queryset,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)
