from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django.urls import reverse
from django.shortcuts import redirect

from .models import Recipe


class RecipeViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticatedOrReadOnly])
    def get_short_link(self, request, id):
        get_object_or_404(Recipe, pk=id)
        short_link = request.build_absolute_uri(reverse(
            'recipe_redirect',
            kwargs={'recipe_id': id}
        ))
        return Response({"short_link": short_link}, status=status.HTTP_200_OK)

def recipe_redirect_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
