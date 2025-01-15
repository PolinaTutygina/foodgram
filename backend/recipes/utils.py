def resolve_placeholders(data):
    
    placeholder_mapping = {
        "firstIndredientId": 1,
        "secondIndredientId": 2,
    }

    for ingredient in data.get('ingredients', []):
        if isinstance(ingredient['id'], str) and ingredient['id'].startswith("{{") and ingredient['id'].endswith("}}"):
            placeholder = ingredient['id'][2:-2]
            ingredient['id'] = placeholder_mapping.get(placeholder)

    return data
