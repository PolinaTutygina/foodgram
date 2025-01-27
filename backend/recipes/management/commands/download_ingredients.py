import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON файла в базу данных'

    def handle(self, *args, **kwargs):
        try:
            with open('ingredients.json', 'r', encoding='utf-8') as file:
                created_ingredients = Ingredient.objects.bulk_create(
                    [Ingredient(**item) for item in json.load(file)],
                    ignore_conflicts=True
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно добавлено {len(created_ingredients)} ингредиентов.'
                )
            )
        except Exception as e:
            self.stderr.write(f'Произошла ошибка: {e}')
