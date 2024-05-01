import re

from django.core.exceptions import ValidationError
from recipes.constants import REGEX_ALLOWS, REGEX_PATTERN


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
