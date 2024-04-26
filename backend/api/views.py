from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
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
    Recipe_Ingredients,
    Subscribe,
    Tag,
    User,
)

from .filter import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permission import IsAuthorOrAdminOrReadOnly
from .serializers import (
    CustomUserSerializer,
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

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def make_shopping_list(self, request):
        """Функция для создания файла со списком покупок."""

        recipes_in_carts = Recipe.objects.filter(carts__user=request.user)
        ingredients = Recipe_Ingredients.objects.filter(
            recipe__in=recipes_in_carts
        ).values(
            'ingredients__name', 'ingredients__measurement_unit'
        ).annotate(ingredients_amount=Sum('amount'))

        shopping_list = ['Список покупок:\n']
        counter = 1
        for ingredient in ingredients:
            name = ingredient['ingredients__name']
            unit = ingredient['ingredients__measurement_unit']
            amount = ingredient['ingredients__amount']
            shopping_list.append(f'\n{counter}. {name} - {amount} {unit}')
            counter += 1
        return shopping_list

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, ]
    )
    def download_shopping_cart(self, request):
        """Отправка файла со списком покупок."""
        response = HttpResponse(self.make_shopping_list(request),
                                content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=('POST', 'DELETE',),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            context = {'request': request}
            try:
                recipe = Recipe.objects.get(id=pk)
            except Recipe.DoesNotExist:
                raise ValidationError("Recipe with given ID does not exist.")
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = ShoppingCartSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            if not Cart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                raise ValidationError(
                    "Recipe with given ID is not in the shopping cart."
                )
            get_object_or_404(
                Cart,
                user=request.user.id,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST', 'DELETE',),
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            context = {"request": request}
            try:
                recipe = Recipe.objects.get(id=pk)
            except Recipe.DoesNotExist:
                raise ValidationError("Recipe with given ID does not exist.")
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = FavoriteSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            if not Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                raise ValidationError(
                    "Recipe with given ID is not in favorites."
                )
            get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    """Вывод пользователей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ('me', 'subscribe'):
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            serializer = SubcribeSerializer(
                author,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            try:
                subscription = Subscribe.objects.get(user=user, author=author)
            except Subscribe.DoesNotExist:
                raise ValidationError("Subscription does not exist.")

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscriptions = request.user.subscriber.all()
        users_id = subscriptions.values_list('author__id', flat=True)
        users = User.objects.filter(id__in=users_id)
        paginated_queryset = self.paginate_queryset(users)
        serializer = SubscriptionSerializer(
            paginated_queryset,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)
