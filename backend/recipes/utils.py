def resolve_placeholders(data):
    placeholder_mapping = {
        "firstIngredientId": 1,
        "secondIngredientId": 2,
    }

    for ingredient in data.get('ingredients', []):
        ingredient_id = ingredient['id']
        if isinstance(ingredient_id, str) and ingredient_id.startswith("{{") \
                and ingredient_id.endswith("}}"):
            placeholder = ingredient_id[2:-2]
            ingredient['id'] = placeholder_mapping.get(placeholder, None)

    data['ingredients'] = [
        ing for ing in data['ingredients'] if ing['id'] is not None
    ]

    return data
