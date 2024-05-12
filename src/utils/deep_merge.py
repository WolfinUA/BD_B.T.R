def deep_merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            deep_merge.__deep_merge(value, destination.setdefault(key, {}))
        elif isinstance(value, list):
            if key not in destination:
                destination[key] = []
            destination[key] += value
        else:
            destination[key] = value
    return destination