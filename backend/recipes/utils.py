def resolve_placeholders(data):

    placeholder_mapping = {
        "firstIndredientId": 1,
        "secondIndredientId": 2,
    }

    for ingredient in data.get('ingredients', []):
        ingredient_id = ingredient['id']
        if isinstance(ingredient_id, str) and ingredient_id.startswith("{{") \
                and ingredient_id.endswith("}}"):
            placeholder = ingredient_id[2:-2]
            ingredient['id'] = placeholder_mapping.get(placeholder)

    return data
