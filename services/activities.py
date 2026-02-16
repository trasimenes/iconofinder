import requests
import re
from config.urls import PARKS_URLS

PRESTATION_API_BASE = "https://prestation-api.groupepvcp.com/v1/activities/cpe"
PHOTOS_BASE_URL = "https://photos.centerparcs.com/admin/"

class ActivityService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'curl/8.7.1',
            'Accept': '*/*'
        })

    def get_urls(self):
        """
        Retourne les URLs des parcs avec leur pays
        """
        urls = {}
        for country, parks in PARKS_URLS.items():
            for park_name, park_urls in parks.items():
                urls[park_name] = {
                    'country': country,
                    'activities': park_urls['activities'],
                    'cottages': park_urls['cottages'],
                    'restaurants': park_urls['restaurants']
                }
        return urls

    def _extract_product_code(self, parc_url):
        """Extract product code from park URL (e.g. 'VN' from fp_VN_...)"""
        match = re.search(r'fp_([A-Z]+)_', parc_url)
        return match.group(1) if match else None

    def _extract_lang_code(self, parc_url):
        """Extract language code from park URL (e.g. 'fr' from /fr-fr/, 'wl' from /be-wl/)"""
        match = re.search(r'centerparcs\.[a-z]+/([a-z]{2})-([a-z]{2})/', parc_url)
        return match.group(2) if match else None

    def _get_photo_path(self, photo):
        """Extract the 500x375 photo path from the API photo dict (values are lists)"""
        if not photo:
            return ''
        paths = photo.get('500x375', [])
        if not paths or not paths[0]:
            return ''
        return paths[0]

    def _has_valid_photo(self, photo):
        """Check if a prestation photo dict contains a valid (non-placeholder) photo"""
        path = self._get_photo_path(photo)
        if not path:
            return False
        if 'default/' in path:
            return False
        return True

    def _build_photo_url(self, photo):
        """Build full photo URL from prestation API photo dict"""
        path = self._get_photo_path(photo)
        if not path:
            return ''
        return PHOTOS_BASE_URL + path

    def get_activities_with_placeholders(self, parc_url):
        """
        Récupère les activités via l'API prestation Center Parcs
        et détecte les images manquantes
        """
        print(f"\n=== ANALYSE DES ACTIVITÉS ===")
        print(f"URL: {parc_url}")

        try:
            product_code = self._extract_product_code(parc_url)
            lang_code = self._extract_lang_code(parc_url)

            if not product_code or not lang_code:
                return {
                    'activities': [],
                    'no_missing_photos': False,
                    'error': f"Impossible d'extraire les paramètres de l'URL: product_code={product_code}, lang_code={lang_code}"
                }

            api_url = f"{PRESTATION_API_BASE}/{lang_code}/SUMMER/{product_code}"
            print(f"API URL: {api_url}")

            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            prestations = data.get('data', {}).get('prestation', [])
            print(f"\nActivités trouvées via API: {len(prestations)}")

            all_activities = []
            for prestation in prestations:
                name = prestation.get('name', 'Activité sans nom')
                photo = prestation.get('photo')
                has_photo = self._has_valid_photo(photo)
                image_url = self._build_photo_url(photo)

                print(f"\nActivité: {name}")
                if has_photo:
                    print(f"  ✅ Photo: {image_url}")
                else:
                    print(f"  ❌ Photo manquante")

                all_activities.append({
                    'name': name,
                    'image_src': image_url or "Pas d'URL d'image",
                    'has_photos': has_photo
                })

            no_missing_photos = all(a['has_photos'] for a in all_activities) if all_activities else True

            return {
                'activities': all_activities,
                'no_missing_photos': no_missing_photos
            }

        except requests.exceptions.ConnectionError as e:
            print(f"Erreur de connexion: {str(e)}")
            return {
                'activities': [],
                'no_missing_photos': False,
                'error': "Impossible de se connecter au site. Veuillez réessayer plus tard."
            }
        except requests.exceptions.Timeout as e:
            print(f"Timeout de la connexion: {str(e)}")
            return {
                'activities': [],
                'no_missing_photos': False,
                'error': "Le site met trop de temps à répondre. Veuillez réessayer plus tard."
            }
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête: {str(e)}")
            return {
                'activities': [],
                'no_missing_photos': False,
                'error': "Une erreur s'est produite lors de la connexion au site."
            }
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'activities': [],
                'no_missing_photos': False,
                'error': error_msg
            }
