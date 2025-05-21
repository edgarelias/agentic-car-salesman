from catalog.models import Vehicle


def get_vehicle_vocab():
    """
    Retrieve unique makes, models, and versions from the Vehicle catalog.
    Returns:
        dict: {'makes': [...], 'models': [...], 'versions': [...]}
    """
    makes = list(Vehicle.objects.values_list('make', flat=True).distinct())
    models = list(Vehicle.objects.values_list('model', flat=True).distinct())
    versions = list(Vehicle.objects.values_list('version', flat=True).distinct())
    return {
        "makes": makes,
        "models": models,
        "versions": versions
    }
