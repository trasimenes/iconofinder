import requests
import re
from bs4 import BeautifulSoup
from config.urls import PARKS_URLS

class ActivityService:
    def __init__(self):
        self.session = requests.Session()
        # Headers minimaux comme curl
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

            # 1. Chercher par éléments <figure> (nouvelle structure du site)
            activity_blocks.extend(soup.find_all('figure'))

            # 2. Chercher par classe contenant "activity" ou "Activity"
            activity_blocks.extend(soup.find_all(class_=lambda x: x and ('activity' in x.lower() or 'Activity' in x)))

            # 3. Chercher par data-attribute
            activity_blocks.extend(soup.find_all(attrs={'data-type': 'activity'}))
            activity_blocks.extend(soup.find_all(attrs={'data-category': 'activity'}))

            # 4. Chercher par structure HTML (div/a avec h2/h3/h4 et img)
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
                picture = block.find('picture')
                source = None

                if picture:
                    # Nouvelle structure avec <picture> et <source>
                    source = picture.find('source')
                    img = picture.find('img')
                else:
                    img = block.find('img')
                    if not img:
                        img_container = block.find(class_=lambda x: x and ('image' in x.lower() or 'photo' in x.lower()))
                        if img_container:
                            picture = img_container.find('picture')
                            if picture:
                                source = picture.find('source')
                                img = picture.find('img')
                            else:
                                img = img_container.find('img')

                if not img:
                    continue

                # Récupérer le titre de l'activité - essayer plusieurs sélecteurs
                title = None
                # 1. Chercher dans <figcaption> (nouvelle structure)
                figcaption = block.find('figcaption')
                if figcaption:
                    title = figcaption
                # 2. Utiliser l'attribut alt de l'image
                if not title and img.get('alt'):
                    title = type('Title', (), {'text': img.get('alt')})()
                # 3. Chercher dans les headings
                if not title:
                    for heading in ['h2', 'h3', 'h4', 'h5']:
                        title_elem = block.find(heading)
                        if title_elem:
                            title = title_elem
                            break
                # 4. Chercher par classe title/name
                if not title:
                    title = block.find(class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                # 5. Utiliser le texte du bloc
                if not title:
                    text_content = block.get_text(strip=True)
                    if text_content:
                        title = type('Title', (), {'text': text_content})()
                activity_name = title.text.strip() if title else "Activité sans nom"

                # Récupérer les URLs d'image depuis plusieurs sources
                src = img.get('src', '')
                data_src = img.get('data-src', '')
                data_url_desktop = img.get('data-url-desktop', '')

                # Récupérer aussi depuis <source> si présent (nouvelle structure)
                srcset = ''
                data_srcset = ''
                if source:
                    srcset = source.get('srcset', '')
                    data_srcset = source.get('data-srcset', '')
                print(f"\nAnalyse de l'activité: {activity_name}")
                print(f"- src: {src}")
                print(f"- data-src: {data_src}")
                print(f"- data-url-desktop: {data_url_desktop}")
                print(f"- srcset: {srcset}")
                print(f"- data-srcset: {data_srcset}")

                # Toutes les sources d'images possibles
                all_sources = [src, data_src, data_url_desktop, srcset, data_srcset]

                # Pattern pour détecter les placeholders :
                # UNIQUEMENT /default/ dans le chemin (ex: /assets/images/default/500x375.jpg)
                # Note: AAA_XXXXX sont des images valides, pas des placeholders
                placeholder_pattern = re.compile(r'/default/', re.IGNORECASE)

                def is_placeholder(url):
                    """Vérifie si une URL est un placeholder"""
                    if not url:
                        return True
                    return bool(placeholder_pattern.search(url))

                is_missing = False
                if not any(all_sources):
                    is_missing = True
                    print("❌ Aucune source d'image trouvée")
                elif all(is_placeholder(url) for url in all_sources if url):
                    is_missing = True
                    print("❌ Image placeholder détectée (/default/)")
                elif all(url == '' for url in all_sources):
                    is_missing = True
                    print("❌ Sources d'images vides")
                else:
                    print("✅ Image valide trouvée")

                if is_missing:
                    no_missing_photos = False

                # Choisir la meilleure source d'image disponible
                best_image = src or data_src or data_url_desktop or srcset or data_srcset or "Pas d'URL d'image"

                all_activities.append({
                    'name': activity_name,
                    'image_src': best_image,
                    'has_photos': not is_missing
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
