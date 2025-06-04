def compute_stats(snapshot_data):
    """Return statistics about missing photos per country and housing type."""
    stats = {
        'activities': {},
        'housings': {},
        'restaurants': {},
        'missing_by_type': {},
        'total_activities': 0,
        'total_housings': 0,
        'total_restaurants': 0,
    }
    default_fragment = 'default/500x375.jpg'

    for country, parks in snapshot_data.get('activities', {}).items():
        for park_data in parks.values():
            for item in park_data.get('activities', []):
                missing = not item.get('has_photos') or default_fragment in item.get('image_src', '')
                if missing:
                    stats['activities'][country] = stats['activities'].get(country, 0) + 1
                    stats['total_activities'] += 1

    for country, parks in snapshot_data.get('housings', {}).items():
        for park_data in parks.values():
            for item in park_data.get('housings', []):
                missing = not item.get('has_photos') or default_fragment in item.get('image_src', '')
                if missing:
                    stats['housings'][country] = stats['housings'].get(country, 0) + 1
                    stats['total_housings'] += 1
                    typ = item.get('type', '?')
                    stats['missing_by_type'][typ] = stats['missing_by_type'].get(typ, 0) + 1

    for country, parks in snapshot_data.get('restaurants', {}).items():
        for park_data in parks.values():
            for item in park_data.get('restaurants', []):
                missing = (
                    not item.get('has_photos')
                    or default_fragment in item.get('image_src', '')
                    or len(item.get('images', [])) == 0
                )
                if missing:
                    stats['restaurants'][country] = stats['restaurants'].get(country, 0) + 1
                    stats['total_restaurants'] += 1

    return stats
