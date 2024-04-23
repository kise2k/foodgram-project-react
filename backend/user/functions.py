import base64
import re

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from recipes.constants import REGEX_ALLOWS, REGEX_PATTERN
from rest_framework import serializers


def sending_confirmation_code(user):
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        subject='Код подтверждения',
        message=f'Ващ код подтверждения {confirmation_code}',
        from_email=f'{settings.DEFAULT_FROM_EMAIL}',
        recipient_list=(user.email,),
        fail_silently=False,
    )


def validate_username(value):
    regex = re.compile(REGEX_PATTERN)
    if value.lower() == 'me':
        raise ValidationError(
            'Имя пользователя me запрещено'
        )
    if not regex.findall(value):
        raise ValidationError(
            (f'Разрешены символы: {REGEX_ALLOWS}')
        )
    return value


class UserValidateMixin:
    @staticmethod
    def validate_username(value):
        return validate_username(value)


def is_authenticated(request):
    return bool(request and request.user.is_authenticated)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
