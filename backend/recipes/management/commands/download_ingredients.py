import json
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON файла в базу данных'

    def handle(self, *args, **kwargs):
        file_path = 'ingredients.json'

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e: 
            self.stderr.write(f'Ошибка чтения JSON файла: {e}')
            return

        ingredients = [Ingredient(**item) for item in data]
        created_ingredients = Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно добавлено {len(created_ingredients)} ингредиентов.'
            )
        )
