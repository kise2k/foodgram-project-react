from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинация для работы с плавающим числом записей."""
    page_size_query_param = 'limit'
