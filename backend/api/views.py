from collections import defaultdict

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.db.models import Sum, Count
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from djoser import views as djoser_views

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
    def make_shopping_list(ingredients_queryset):
        """Функция для создания списка покупок."""
        ingredients_dict = defaultdict(int)

        for ingredient in ingredients_queryset:
            ingredients_dict[
                ingredient['ingredients__name']
            ] += ingredient['amount']

        shopping_list = ['Список покупок:\n']

        for counter, (name, amount) in enumerate(
            ingredients_dict.items(),
            start=1
        ):
            shopping_list.append(
                f'\n{counter}. {name} - '
                f'{amount} {ingredient["ingredients__measurement_unit"]}'
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
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredients__name')

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
        try:
            Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"error": "Рецепт с указанным ID не найден."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return FavoriteSerializer.create_instance(
            FavoriteSerializer,
            pk,
            request
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаление рецепта из избранного."""
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"error": "Рецепт с указанным ID не найден!"},
                status=status.HTTP_404_NOT_FOUND
            )
        if not Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            raise ValidationError("Рецепт не найден в избранном.")
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добавление рецепта в список покупок."""
        try:
            Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"error": "Рецепт с указанным ID не найден."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return ShoppingCartSerializer.create_instance(
            ShoppingCartSerializer,
            pk,
            request
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаление рецепта из списка покупок."""
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"error": "Рецепт с указанным ID не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        if not Cart.objects.filter(user=request.user, recipe=recipe).exists():
            raise ValidationError("Рецепт не найден в списке покупок.")
        Cart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(djoser_views.UserViewSet):
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
        try:
            User.objects.get(pk=id)
        except User.DoesNotExist:
            return Response(
                {"error": "Автор с указанным ID не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = SubcribeSerializer(
            data={'user': request.user.id, 'author': id},
            context={'request': request, 'id': id}
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
            recipe_count=Count('recipes', distinct=True)
        )
        paginated_queryset = self.paginate_queryset(users)
        serializer = SubscriptionSerializer(
            paginated_queryset,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)
