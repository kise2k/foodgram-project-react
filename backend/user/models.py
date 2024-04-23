from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constants import FIELD_LEN_150, FIELD_LEN_254

from .functions import validate_username


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Почта пользователя',
        max_length=FIELD_LEN_254,
        unique=True
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=FIELD_LEN_150,
        unique=True,
        validators=[validate_username]
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=FIELD_LEN_150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=FIELD_LEN_150,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=FIELD_LEN_150,
    )
    REQUIRED_FIELDS = [
        'id',
        'username',
        'first_name',
        'last_name'
    ]
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
