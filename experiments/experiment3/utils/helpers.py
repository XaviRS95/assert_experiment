# Any additional helper functions that don't fit elsewhere
def safe_get(data: dict, key: str, default=None):
    """Safely get value from dictionary"""
    return data.get(key, default) if data else default

def ensure_list(item):
    """Ensure item is a list"""
    if item is None:
        return []
    return item if isinstance(item, list) else [item]