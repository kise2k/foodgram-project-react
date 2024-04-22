from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RecipeViewSet,
    TagViewSet,
    IngredientViewSet,
    CustomUserViewSet
)

router_ver_1 = DefaultRouter()

router_ver_1.register(
    r'recipes',
    RecipeViewSet,
    basename='recipe'
)
router_ver_1.register(
    r'tags',
    TagViewSet,
    basename='tag'
)
router_ver_1.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredient'
)
router_ver_1.register(
    r'users',
    CustomUserViewSet,
    basename='user'
)
urlpatterns = [
    path('', include(router_ver_1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
