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
                        {'name': 'Act1', 'has_photos': False, 'image_src': ''},
                        {'name': 'Act1', 'has_photos': True, 'image_src': 'ok.jpg'}
                    ]
                }
            }
        },
        'housings': {
            'FR': {
                'Park': {
                    'housings': [
                        {'name': 'Hou1', 'has_photos': False, 'image_src': 'default/500x375.jpg', 'type': 'VIP'},
                        {'name': 'Hou1', 'has_photos': True, 'image_src': 'ok.jpg', 'type': 'VIP'}
                    ]
                }
            }
        },
        'restaurants': {
            'FR': {
                'Park': {
                    'restaurants': [
                        {'name': 'Res1', 'has_photos': False, 'images': []},
                        {'name': 'Res1', 'has_photos': True, 'images': ['ok.jpg']}
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
    assert dict(stats['top_activities'])['Act1'] == 1
    assert dict(stats['top_housings'])['Hou1'] == 1
    assert dict(stats['top_restaurants'])['Res1'] == 1

def test_compute_stats_top_counts():
    data = {
        'activities': {
            'FR': {
                'Park': {
                    'activities': [
                        {'name': 'A1', 'has_photos': False, 'image_src': ''},
                        {'name': 'A1', 'has_photos': False, 'image_src': ''},
                        {'name': 'A2', 'has_photos': False, 'image_src': ''}
                    ]
                }
            }
        },
        'housings': {
            'FR': {
                'Park': {
                    'housings': [
                        {'name': 'H1', 'has_photos': False, 'image_src': 'default/500x375.jpg', 'type': 'VIP'},
                        {'name': 'H1', 'has_photos': False, 'image_src': 'default/500x375.jpg', 'type': 'VIP'}
                    ]
                }
            }
        },
        'restaurants': {
            'FR': {
                'Park': {
                    'restaurants': [
                        {'name': 'R1', 'has_photos': False, 'images': []},
                        {'name': 'R1', 'has_photos': False, 'images': []}
                    ]
                }
            }
        }
    }
    stats = compute_stats(data)
    assert dict(stats['top_activities'])['A1'] == 2
    assert dict(stats['top_housings'])['H1'] == 2
    assert dict(stats['top_restaurants'])['R1'] == 2

