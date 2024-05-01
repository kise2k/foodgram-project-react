from csv import reader
from typing import Any

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient, Tag

CSV_FILES = {
    'ingredients.csv': (Ingredient, 2),
    'tags.csv': (Tag, 3),
}


class Command(BaseCommand):
    help = 'Импорт данных из csv файлов в БД'

    def handle(self, *args: Any, **options: Any) -> str:
        for file, (model, num_fields) in CSV_FILES.items():
            try:
                with open(
                    f'./static/data/{file}',
                    encoding='utf-8'
                ) as csv_file:
                    csv_reader = reader(csv_file)
                    next(csv_reader)

                    objects_to_create = [
                        self.create_object(model, row[:num_fields])
                        for row in csv_reader
                    ]

                    model.objects.bulk_create(objects_to_create)

                self.stderr.write(f'Данные из файла {file} успешно загружены')

            except FileNotFoundError:
                self.stderr.write(f'Файл {file} не найден')
            except IntegrityError:
                self.stderr.write(f'Файл {file} уже был загружен')

    def create_object(self, model, data):
        if len(data) == 2:
            name, measurement_unit = data
            return model(
                name=name,
                measurement_unit=measurement_unit
            )
        name, color, slug = data
        return model(
                name=name,
                color=color,
                slug=slug
            )
