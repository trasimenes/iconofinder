import requests
from bs4 import BeautifulSoup
from config.urls import PARKS_URLS

class ActivityService:
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

    def get_activities_with_placeholders(self, parc_url):
        """
        Récupère les activités qui ont des images manquantes
        """
        print(f"\n=== ANALYSE DES ACTIVITÉS ===")
        print(f"URL: {parc_url}")
        
        try:
            response = self.session.get(parc_url, timeout=30)  # Ajout d'un timeout de 30 secondes
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher tous les blocs d'activités avec différentes approches
            activity_blocks = []
            
            # 1. Chercher par classe contenant "activity" ou "Activity"
            activity_blocks.extend(soup.find_all(class_=lambda x: x and ('activity' in x.lower() or 'Activity' in x)))
            
            # 2. Chercher par data-attribute
            activity_blocks.extend(soup.find_all(attrs={'data-type': 'activity'}))
            activity_blocks.extend(soup.find_all(attrs={'data-category': 'activity'}))
            
            # 3. Chercher par structure HTML (div/a avec h2/h3/h4 et img)
            for element in soup.find_all(['div', 'a']):
                if (element.find(['h2', 'h3', 'h4']) and element.find('img')):
                    activity_blocks.append(element)
            
            # Dédupliquer les blocs trouvés
            activity_blocks = list(set(activity_blocks))
            
            print(f"\nBlocs d'activités trouvés: {len(activity_blocks)}")
            
            # Afficher un échantillon du HTML pour déboguer
            print("\nÉchantillon du HTML:")
            print(soup.prettify()[:1000])
            
            all_activities = []
            no_missing_photos = True
            for block in activity_blocks:
                # Chercher l'image avec différentes approches
                img = None
                img = block.find('img')
                if not img:
                    img_container = block.find(class_=lambda x: x and ('image' in x.lower() or 'photo' in x.lower()))
                    if img_container:
                        img = img_container.find('img')
                if not img:
                    continue
                # Récupérer le titre de l'activité - essayer plusieurs sélecteurs
                title = None
                if img.get('alt'):
                    title = type('Title', (), {'text': img.get('alt')})()
                if not title:
                    for heading in ['h2', 'h3', 'h4', 'h5']:
                        title_elem = block.find(heading)
                        if title_elem:
                            title = title_elem
                            break
                if not title:
                    title = block.find(class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                if not title:
                    text_content = block.get_text(strip=True)
                    if text_content:
                        title = type('Title', (), {'text': text_content})()
                activity_name = title.text.strip() if title else "Activité sans nom"
                src = img.get('src', '')
                data_src = img.get('data-src', '')
                data_url_desktop = img.get('data-url-desktop', '')
                print(f"\nAnalyse de l'activité: {activity_name}")
                print(f"- src: {src}")
                print(f"- data-src: {data_src}")
                print(f"- data-url-desktop: {data_url_desktop}")
                is_missing = False
                if not (src or data_src or data_url_desktop):
                    is_missing = True
                    print("❌ Aucune source d'image trouvée")
                elif all(('default' in url.lower() if url else True) for url in [src, data_src, data_url_desktop]):
                    is_missing = True
                    print("❌ Image par défaut détectée")
                elif all(url == '' for url in [src, data_src, data_url_desktop]):
                    is_missing = True
                    print("❌ Sources d'images vides")
                else:
                    print("✅ Image valide trouvée")
                if is_missing:
                    no_missing_photos = False
                all_activities.append({
                    'name': activity_name,
                    'image_src': src or data_src or data_url_desktop or "Pas d'URL d'image",
                    'has_photo': not is_missing
                })
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
