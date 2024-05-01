from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

from recipes.constants import FIELD_LEN_FOR_USER_MODEL, FIELD_LEN_EMAIL
from .functions import validate_username


class User(AbstractUser):
    REQUIRED_FIELDS = (
        'id',
        'username',
        'first_name',
        'last_name'
    )
    USERNAME_FIELD = 'email'
    email = models.EmailField(
        verbose_name='Почта пользователя',
        max_length=FIELD_LEN_EMAIL,
        unique=True
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=FIELD_LEN_FOR_USER_MODEL,
        unique=True,
        validators=(validate_username,)
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=FIELD_LEN_FOR_USER_MODEL,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=FIELD_LEN_FOR_USER_MODEL,
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель описывающая подписки."""
    user = models.ForeignKey(
        User,
        related_name='subscriber',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='subscribing',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('user', 'author',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_user_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписываться на самого себя')

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
