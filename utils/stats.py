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
        'top_activities_by_country': {},
    }
    default_fragment = 'default/500x375.jpg'
    activity_counter = Counter()
    housing_counter = Counter()
    restaurant_counter = Counter()
    activity_counters_by_country = {}

    for country, parks in snapshot_data.get('activities', {}).items():
        if country not in activity_counters_by_country:
            activity_counters_by_country[country] = Counter()
            
        for park_data in parks.values():
            for item in park_data.get('activities', []):
                image_src = item.get('image_src', '')
                missing = (
                    not image_src or 
                    default_fragment in image_src or
                    'default/' in image_src
                )
                
                if missing:
                    stats['activities'][country] = stats['activities'].get(country, 0) + 1
                    stats['total_activities'] += 1
                    if item.get('name'):
                        activity_counter[item['name']] += 1
                        activity_counters_by_country[country][item['name']] += 1
    
    # S'assurer que tous les pays sont dans activity_counters_by_country même sans activités manquantes
    for country in snapshot_data.get('activities', {}).keys():
        if country not in activity_counters_by_country:
            activity_counters_by_country[country] = Counter()

    for country, parks in snapshot_data.get('housings', {}).items():
        for park_data in parks.values():
            for item in park_data.get('housings', []):
                if 'has_photos' in item:
                    missing = not item.get('has_photos')
                else:
                    image_src = item.get('image_src', '')
                    missing = (
                        not image_src or 
                        default_fragment in image_src or
                        'default/' in image_src
                    )
                
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
                if 'has_photos' in item:
                    missing = not item.get('has_photos')
                else:
                    image_src = item.get('image_src', '')
                    missing = (
                        not image_src or 
                        default_fragment in image_src or
                        'default/' in image_src or
                        len(item.get('images', [])) == 0
                    )
                
                if missing:
                    stats['restaurants'][country] = stats['restaurants'].get(country, 0) + 1
                    stats['total_restaurants'] += 1
                    if item.get('name'):
                        restaurant_counter[item['name']] += 1

    # Filtrer pour ne montrer que les éléments manquants plus d'une fois
    stats['top_activities'] = [(name, count) for name, count in activity_counter.most_common(5) if count > 1]
    stats['top_housings'] = [(name, count) for name, count in housing_counter.most_common(5) if count > 1]
    stats['top_restaurants'] = [(name, count) for name, count in restaurant_counter.most_common(5) if count > 1]
    overall_counter = activity_counter + housing_counter + restaurant_counter
    stats['top_missing_items'] = [(name, count) for name, count in overall_counter.most_common(5) if count > 1]
    
    # Top 3 activities par pays (même avec 1 seule occurrence)
    for country, counter in activity_counters_by_country.items():
        stats['top_activities_by_country'][country] = counter.most_common(3)

    return stats
