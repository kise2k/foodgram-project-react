from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AdminForUserBase
from django.db.models import Count

from .models import User, Subscribe


@admin.register(User)
class UserAdmin(AdminForUserBase):
    """Класс админ-интерфейса для раздела пользователей."""

    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
        'get_recipe_count',
        'get_subscriber_count',
    )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_display_links = ('username',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            recipe_count=Count('recipes', distinct=True),
            subscriber_count=Count('subscribing', distinct=True)
        )
        return queryset

    @admin.display(description='Кол-во рецептов')
    def get_recipe_count(self, obj):
        return obj.recipe_count

    @admin.display(description='Кол-во подписчиков')
    def get_subscriber_count(self, obj):
        return obj.subscriber_count


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')
