from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class MyUserAdmin(UserAdmin):
    """Класс админ-интерфейса для раздела пользователей."""

    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_display_links = ('username',)
