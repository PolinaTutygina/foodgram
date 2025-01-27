from django.shortcuts import redirect, get_object_or_404
from .models import Recipe

def recipe_redirect_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
