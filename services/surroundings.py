import requests
import re
from bs4 import BeautifulSoup


class SurroundingsService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'curl/8.7.1',
            'Accept': '*/*'
        })

    def get_surroundings_with_placeholders(self, parc_url):
        """
        Récupère les points d'intérêt "Aux alentours" qui ont des images manquantes
        """
        print(f"\n=== ANALYSE DES ALENTOURS ===")
        print(f"URL: {parc_url}")

        try:
            response = self.session.get(parc_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Chercher tous les blocs de POI (Points of Interest)
            poi_blocks = []

            # 1. Chercher par éléments <figure> (structure standard)
            poi_blocks.extend(soup.find_all('figure'))

            # 2. Chercher par classe contenant "poi" ou "surrounding"
            poi_blocks.extend(soup.find_all(class_=lambda x: x and ('poi' in x.lower() or 'surrounding' in x.lower())))

            # 3. Chercher par data-attribute
            poi_blocks.extend(soup.find_all(attrs={'data-type': 'poi'}))
            poi_blocks.extend(soup.find_all(attrs={'data-category': 'poi'}))

            # 4. Chercher par structure HTML (div/a avec h2/h3/h4 et img)
            for element in soup.find_all(['div', 'a', 'article']):
                if element.find(['h2', 'h3', 'h4']) and element.find('img'):
                    poi_blocks.append(element)

            # Dédupliquer les blocs trouvés
            poi_blocks = list(set(poi_blocks))

            print(f"\nBlocs POI trouvés: {len(poi_blocks)}")

            all_surroundings = []
            no_missing_photos = True

            for block in poi_blocks:
                # Chercher l'image avec différentes approches
                img = None
                picture = block.find('picture')
                source = None

                if picture:
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

                # Récupérer le titre du POI
                title = None
                # 1. Chercher dans <figcaption>
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

                poi_name = title.text.strip() if title else "Lieu sans nom"

                # Nettoyer le nom : retirer le nom du parc s'il est à la fin
                park_names = [
                    "Villages Nature Paris", "Le Lac d'Ailette", "Les Hauts de Bruyères",
                    "Le Bois aux Daims", "Les Bois-Francs", "Les Trois Forêts", "Les Landes de Gascogne",
                    "Les Ardennes", "De Vossemeren", "Erperheide", "Park De Haan", "Terhills Resort",
                    "Park Bostalsee", "Park Hochsauerland", "Park Allgäu", "Bispinger Heide",
                    "Park Nordseeküste", "Park Eifel",
                    "Port Zélande", "Het Heijderbos", "Park Zandvoort", "De Kempervennen",
                    "De Huttenheugte", "De Eemhof", "Het Meerdal", "Parc Sandur", "Limburgse Peel",
                    "Nordborg Resort"
                ]
                for park in park_names:
                    if poi_name.endswith(park):
                        poi_name = poi_name[:-len(park)].strip()
                        break

                # Récupérer les URLs d'image depuis plusieurs sources
                src = img.get('src', '')
                data_src = img.get('data-src', '')
                data_url_desktop = img.get('data-url-desktop', '')

                # Récupérer aussi depuis <source> si présent
                srcset = ''
                data_srcset = ''
                if source:
                    srcset = source.get('srcset', '')
                    data_srcset = source.get('data-srcset', '')

                print(f"\nAnalyse du lieu: {poi_name}")
                print(f"- src: {src}")
                print(f"- data-src: {data_src}")

                # Toutes les sources d'images possibles
                all_sources = [src, data_src, data_url_desktop, srcset, data_srcset]

                # Pattern pour détecter les placeholders
                placeholder_pattern = re.compile(r'/default/', re.IGNORECASE)

                def is_placeholder(url):
                    if not url:
                        return True
                    return bool(placeholder_pattern.search(url))

                is_missing = False
                if not any(all_sources):
                    is_missing = True
                    print("Aucune source d'image trouvée")
                elif all(is_placeholder(url) for url in all_sources if url):
                    is_missing = True
                    print("Image placeholder détectée (/default/)")
                elif all(url == '' for url in all_sources):
                    is_missing = True
                    print("Sources d'images vides")
                else:
                    print("Image valide trouvée")

                if is_missing:
                    no_missing_photos = False

                # Choisir la meilleure source d'image disponible
                best_image = src or data_src or data_url_desktop or srcset or data_srcset or "Pas d'URL d'image"

                all_surroundings.append({
                    'name': poi_name,
                    'image_src': best_image,
                    'has_photos': not is_missing
                })

            # Dédupliquer par nom (garder la première occurrence)
            seen_names = set()
            unique_surroundings = []
            for item in all_surroundings:
                if item['name'] not in seen_names:
                    seen_names.add(item['name'])
                    unique_surroundings.append(item)

            # Recalculer no_missing_photos après déduplication
            no_missing_photos = all(s['has_photos'] for s in unique_surroundings) if unique_surroundings else True

            return {
                'surroundings': unique_surroundings,
                'no_missing_photos': no_missing_photos
            }

        except requests.exceptions.ConnectionError as e:
            print(f"Erreur de connexion: {str(e)}")
            return {
                'surroundings': [],
                'no_missing_photos': False,
                'error': "Impossible de se connecter au site."
            }
        except requests.exceptions.Timeout as e:
            print(f"Timeout: {str(e)}")
            return {
                'surroundings': [],
                'no_missing_photos': False,
                'error': "Le site met trop de temps à répondre."
            }
        except requests.exceptions.RequestException as e:
            print(f"Erreur requête: {str(e)}")
            return {
                'surroundings': [],
                'no_missing_photos': False,
                'error': "Erreur lors de la connexion au site."
            }
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            print(f"{error_msg}")
            return {
                'surroundings': [],
                'no_missing_photos': False,
                'error': error_msg
            }
