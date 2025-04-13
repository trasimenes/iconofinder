import requests
from bs4 import BeautifulSoup
from config.urls import PARKS_URLS

class RestaurantService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

    def get_restaurants_with_placeholders(self, parc_url):
        """
        Récupère les restaurants qui ont des images manquantes
        """
        try:
            print(f"\n=== ANALYSE DES RESTAURANTS ===")
            print(f"URL: {parc_url}")
            
            response = self.session.get(parc_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher tous les blocs de restaurants
            restaurant_blocks = soup.find_all(['div', 'article'], class_=lambda x: x and ('restaurant' in x.lower() or 'resto' in x.lower()))
            total_restaurants = len(restaurant_blocks)
            print(f"\nTotal des restaurants trouvés: {total_restaurants}")
            
            # Liste pour stocker les restaurants
            restaurants_with_placeholders = []
            no_missing_photos = True
            
            # Pour chaque bloc de restaurant
            for block in restaurant_blocks:
                # Chercher le titre
                title_element = block.find(['h2', 'h3', 'h4'])
                restaurant_name = title_element.text.strip() if title_element else "Restaurant sans nom"
                
                print(f"\n=== Analyse de: {restaurant_name} ===")
                
                # Chercher les images
                all_images = block.find_all('img')
                print(f"Images trouvées: {len(all_images)}")
                
                # Détails de chaque image trouvée
                has_photos = False  # Par défaut, on suppose qu'il n'y a pas de photos
                
                # Analyse des images trouvées
                for img in all_images:
                    src = img.get('src', '')
                    data_src = img.get('data-src', '')
                    data_url_desktop = img.get('data-url-desktop', '')
                    
                    # Une image est valide si elle a une URL et ne contient pas "default"
                    is_valid = False
                    
                    # Vérifier data-src
                    if data_src and "default" not in data_src.lower():
                        if "photos.centerparcs.com" in data_src or "fp2/photos" in data_src:
                            has_photos = True
                            break
                    
                    # Vérifier src
                    if src and "default" not in src.lower():
                        if "photos.centerparcs.com" in src or "fp2/photos" in src:
                            has_photos = True
                            break
                    
                    # Vérifier data-url-desktop
                    if data_url_desktop and "default" not in data_url_desktop.lower():
                        if "photos.centerparcs.com" in data_url_desktop or "fp2/photos" in data_url_desktop:
                            has_photos = True
                            break
                
                if not has_photos:
                    no_missing_photos = False
                    restaurants_with_placeholders.append({
                        'name': restaurant_name
                    })
                    print(f"❌ Pas de photos valides pour {restaurant_name}")
                else:
                    print(f"✅ Photos valides trouvées pour {restaurant_name}")
            
            return {
                'activities': restaurants_with_placeholders,
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