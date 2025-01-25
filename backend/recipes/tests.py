from django.test import TestCase
from recipes.models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
)
from users.models import User


class RecipeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='chef',
            password='pass123',
        )
        self.ingredient = Ingredient.objects.create(
            name='Sugar',
            measurement_unit='grams',
        )
        self.recipe = Recipe.objects.create(
            author=self.user,
            title='Cake',
            image='test_image.jpg',
            description='Delicious cake recipe',
            cooking_time=60,
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=100,
        )

    def test_recipe_creation(self):
        """Тест создания рецепта."""
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(self.recipe.title, 'Cake')
        self.assertEqual(self.recipe.cooking_time, 60)

    def test_ingredient_association(self):
        """Тест связи рецепта с ингредиентом."""
        self.assertTrue(
            self.recipe.ingredients.filter(name='Sugar').exists()
        )
        recipe_ingredient = RecipeIngredient.objects.get(
            recipe=self.recipe,
            ingredient=self.ingredient,
        )
        self.assertEqual(recipe_ingredient.amount, 100)
