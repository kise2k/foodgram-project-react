import csv
from typing import Any

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient

CSV_FILES = {
    'ingredients.csv': Ingredient,
}


class Command(BaseCommand):
    help = 'Импорт данных из csv файлов в БД'

    def handle(self, *args: Any, **options: Any) -> str | None:
        for file, model in CSV_FILES.items():
            try:
                with open(
                    f'./static/data/{file}', encoding='utf-8'
                ) as csv_file:
                    reader = csv.DictReader(csv_file)
                    model.objects.bulk_create(
                        model(name=row[0], measurement_unit=row[1])
                        for row in reader(csv_file)
                    )
                self.stderr.write(f'Данные из файла {file} успешно загружены')

            except FileNotFoundError:
                self.stderr.write(f'Файл {file} не найден')
            except IntegrityError:
                self.stderr.write(f'Файл {file} уже был загружен')
