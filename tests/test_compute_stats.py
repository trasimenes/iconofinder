import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.stats import compute_stats

def test_compute_stats_basic():
    data = {
        'activities': {
            'FR': {
                'Park': {
                    'activities': [
                        {'has_photos': False, 'image_src': ''},
                        {'has_photos': True, 'image_src': 'ok.jpg'}
                    ]
                }
            }
        },
        'housings': {
            'FR': {
                'Park': {
                    'housings': [
                        {'has_photos': False, 'image_src': 'default/500x375.jpg', 'type': 'VIP'},
                        {'has_photos': True, 'image_src': 'ok.jpg', 'type': 'VIP'}
                    ]
                }
            }
        },
        'restaurants': {
            'FR': {
                'Park': {
                    'restaurants': [
                        {'has_photos': False, 'images': []},
                        {'has_photos': True, 'images': ['ok.jpg']}
                    ]
                }
            }
        }
    }
    stats = compute_stats(data)
    assert stats['activities']['FR'] == 1
    assert stats['housings']['FR'] == 1
    assert stats['restaurants']['FR'] == 1
    assert stats['missing_by_type']['VIP'] == 1
    assert stats['total_activities'] == 1
    assert stats['total_housings'] == 1
    assert stats['total_restaurants'] == 1

