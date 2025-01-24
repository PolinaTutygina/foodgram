import json
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON файла в базу данных'

    def handle(self, *args, **kwargs):
        file_path = 'ingredients.json'

        if not os.path.exists(file_path):
            self.stderr.write(f'Файл {file_path} не найден.')
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                self.stderr.write(f'Ошибка чтения JSON файла: {e}')
                return

        created_count = 0
        for item in data:
            if 'name' in item and 'measurement_unit' in item:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                if created:
                    created_count += 1
            else:
                self.stderr.write(f'Пропущен элемент с отсутствующими данными: {item}')

        self.stdout.write(
            self.style.SUCCESS(f'Успешно добавлено {created_count} ингредиентов.')
        )
