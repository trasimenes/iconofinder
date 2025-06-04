from collections import Counter


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
        'top_activities': [],
        'top_housings': [],
        'top_restaurants': [],
        'top_missing_items': [],
    }
    default_fragment = 'default/500x375.jpg'
    activity_counter = Counter()
    housing_counter = Counter()
    restaurant_counter = Counter()

    for country, parks in snapshot_data.get('activities', {}).items():
        for park_data in parks.values():
            for item in park_data.get('activities', []):
                missing = not item.get('has_photos') or default_fragment in item.get('image_src', '')
                if missing:
                    stats['activities'][country] = stats['activities'].get(country, 0) + 1
                    stats['total_activities'] += 1
                    if item.get('name'):
                        activity_counter[item['name']] += 1

    for country, parks in snapshot_data.get('housings', {}).items():
        for park_data in parks.values():
            for item in park_data.get('housings', []):
                missing = not item.get('has_photos') or default_fragment in item.get('image_src', '')
                if missing:
                    stats['housings'][country] = stats['housings'].get(country, 0) + 1
                    stats['total_housings'] += 1
                    typ = item.get('type', '?')
                    stats['missing_by_type'][typ] = stats['missing_by_type'].get(typ, 0) + 1
                    if item.get('name'):
                        housing_counter[item['name']] += 1

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
                    if item.get('name'):
                        restaurant_counter[item['name']] += 1

    stats['top_activities'] = activity_counter.most_common(5)
    stats['top_housings'] = housing_counter.most_common(5)
    stats['top_restaurants'] = restaurant_counter.most_common(5)
    overall_counter = activity_counter + housing_counter + restaurant_counter
    stats['top_missing_items'] = overall_counter.most_common(5)

    return stats
