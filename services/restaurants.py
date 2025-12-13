"""
Extraction factorisée des offres (restaurants, supermarchés, forfaits, services).
Utilisation :
    - RestaurantService().get_all_offers(parc_url) -> liste d'offres détaillées
    - group_offers_by_typology(offers) -> dict par typologie pour l'UI/API
Chaque offre contient :
    type, name, description, images, cuisine_type, horaires, link, has_photos
"""
import requests
from bs4 import BeautifulSoup
from config.urls import PARKS_URLS

def _get_img_url(img):
    """
    Récupère l'URL d'une image, qu'elle soit en data-src, src, data-srcset, srcset (lazy loading),
    et gère aussi les balises <source>.
    """
    if not img:
        return None
    # Pour <img>
    if img.has_attr('data-src'):
        return img['data-src']
    if img.has_attr('src'):
        return img['src']
    if img.has_attr('data-srcset'):
        return img['data-srcset'].split()[0]
    if img.has_attr('srcset'):
        return img['srcset'].split()[0]
    # Pour <source>
    if img.name == 'source':
        if img.has_attr('data-srcset'):
            return img['data-srcset'].split()[0]
        if img.has_attr('srcset'):
            return img['srcset'].split()[0]
    return None

class RestaurantService:
    def __init__(self):
        self.session = requests.Session()
        # Headers minimaux comme curl pour éviter les 403
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

    def get_restaurants_with_placeholders(self, parc_url):
        """
        Récupère toutes les offres (restaurants, supermarchés, forfaits, services) avec détection robuste des photos manquantes.
        """
        try:
            print(f"\n=== ANALYSE DES OFFRES (TOUTES TYPOLOGIES) ===")
            print(f"URL: {parc_url}")
            response = self.session.get(parc_url)
            response.raise_for_status()
            html = response.content
            all_offers = self.extract_all_offers(html)
            # On ne filtre plus, on retourne tout (restaurants, supermarchés, forfaits, services)
            typologies = {'restaurants': [], 'supermarches': [], 'forfaits': [], 'services': []}
            no_missing_photos = True
            for offer in all_offers:
                if not offer['has_photos']:
                    no_missing_photos = False
                if offer['type'] == 'restaurant':
                    typologies['restaurants'].append(offer)
                elif offer['type'] == 'supermarche':
                    typologies['supermarches'].append(offer)
                elif offer['type'] == 'forfait':
                    typologies['forfaits'].append(offer)
                elif offer['type'] == 'service':
                    typologies['services'].append(offer)
            return {
                'restaurants': typologies['restaurants'],
                'supermarches': typologies['supermarches'],
                'forfaits': typologies['forfaits'],
                'services': typologies['services'],
                'no_missing_photos': no_missing_photos
            }
        except requests.exceptions.ConnectionError as e:
            print(f"Erreur de connexion: {str(e)}")
            return {
                'restaurants': [],
                'supermarches': [],
                'forfaits': [],
                'services': [],
                'no_missing_photos': False,
                'error': "Impossible de se connecter au site. Veuillez réessayer plus tard."
            }
        except requests.exceptions.Timeout as e:
            print(f"Timeout de la connexion: {str(e)}")
            return {
                'restaurants': [],
                'supermarches': [],
                'forfaits': [],
                'services': [],
                'no_missing_photos': False,
                'error': "Le site met trop de temps à répondre. Veuillez réessayer plus tard."
            }
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête: {str(e)}")
            return {
                'restaurants': [],
                'supermarches': [],
                'forfaits': [],
                'services': [],
                'no_missing_photos': False,
                'error': "Une erreur s'est produite lors de la connexion au site."
            }
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'restaurants': [],
                'supermarches': [],
                'forfaits': [],
                'services': [],
                'no_missing_photos': False,
                'error': error_msg
            }

    def extract_cards_with_popin(self, soup, card_selector, type_label):
        results = []
        for card in soup.select(card_selector):
            name = card.select_one('.h4-like, .xp-title')
            img = card.select_one('img')
            popin_id = card.get('data-src', '').replace('#', '')
            popin = soup.find('div', id=popin_id)
            desc = popin.select_one('.popinGeneric-desc') if popin else None
            popin_title = popin.select_one('.popinGeneric-title') if popin else None
            popin_imgs = [img.get('data-src') or img.get('src') for img in popin.select('img')] if popin else []

            results.append({
                "type": type_label,
                "name": name.text.strip() if name else "",
                "image": img.get('src') if img else "",
                "description": desc.text.strip() if desc else "",
                "popin_title": popin_title.text.strip() if popin_title else "",
                "popin_images": popin_imgs,
            })
        return results

    def extract_all_offers(self, html):
        soup = BeautifulSoup(html, "html.parser")
        offers = []
        # Lister tous les blocs principaux
        for bloc in soup.select('div.gb.js-gb'):
            # Déterminer la typologie
            classes = bloc.get("class", [])
            typologie = None
            if "prestas-highlight" in classes:
                typologie = "restaurant"
            elif "prestas-package" in classes:
                typologie = "forfait"
            elif "prestas-commerces" in classes:
                typologie = "supermarche"
            elif "prestas-services" in classes:
                typologie = "service"
            # Si pas trouvé, essayer par titre
            if not typologie:
                titre = bloc.select_one(".gb-title")
                if titre:
                    titre_txt = titre.get_text(strip=True).lower()
                    if "restaurant" in titre_txt:
                        typologie = "restaurant"
                    elif "forfait" in titre_txt:
                        typologie = "forfait"
                    elif "supermarché" in titre_txt or "boutique" in titre_txt:
                        typologie = "supermarche"
                    elif "service" in titre_txt:
                        typologie = "service"
            # Extraction des items selon le type de bloc
            # Restaurants: a.cardBlocks-blockPictures
            if typologie == "restaurant":
                for a in bloc.select('a.cardBlocks-blockPictures'):
                    offer = self._extract_offer_from_card(a, soup, typologie)
                    offers.append(offer)
            # Forfaits, supermarchés, services: div.xp.js-xp
            else:
                for div in bloc.select('div.xp.js-xp'):
                    offer = self._extract_offer_from_card(div, soup, typologie)
                    offers.append(offer)
        return offers

    def _extract_offer_from_card(self, card, soup, typologie):
        name = card.select_one('.h4-like, .xp-title')
        sub_title = card.select_one('.subTitle')
        img = card.select_one('img')
        img_url = _get_img_url(img)
        # Si pas d'image trouvée, cherche un <source> frère ou parent
        if not img_url:
            # Cherche un <source> dans le même parent
            parent = img.parent if img else card
            source = parent.select_one('source') if parent else None
            img_url = _get_img_url(source)
        popin_id = card.get('data-src', '').replace('#', '')
        popin = soup.find('div', id=popin_id) if popin_id else None
        description = ''
        horaires = ''
        menu_link = ''
        popin_images = []
        if popin:
            desc = popin.select_one('.popinGeneric-desc')
            description = desc.get_text(strip=True) if desc else ''
            horaires_tag = popin.select_one('.popinGeneric-detail--list p')
            horaires = horaires_tag.get_text(strip=True) if horaires_tag else ''
            link_tag = popin.select_one('a.popinGeneric-itinerary--link')
            menu_link = link_tag['href'] if link_tag and link_tag.has_attr('href') else ''
            popin_images = [
                _get_img_url(img)
                for img in popin.select('img, source')
                if _get_img_url(img)
            ]
        # Correction : considère une photo présente seulement si img_url est non vide et ne contient pas /default/
        # Note: AAA_XXXXX sont des images valides, pas des placeholders
        def is_valid_photo(url):
            return url and url.strip() and '/default/' not in url.lower()

        has_photos = bool(is_valid_photo(img_url) or (popin_images and any(is_valid_photo(img) for img in popin_images if img)))
        # DEBUG
        print(f"DEBUG {name.get_text(strip=True) if name else ''} | img_url: {img_url} | popin_images: {popin_images} | has_photos: {has_photos}")
        return {
            'type': typologie,
            'name': name.get_text(strip=True) if name else '',
            'description': description,
            'images': [img_url] + popin_images if img_url else popin_images,
            'cuisine_type': sub_title.get_text(strip=True) if sub_title else '',
            'horaires': horaires,
            'link': menu_link,
            'has_photos': has_photos
        }

    def get_all_offers(self, parc_url):
        try:
            print(f"\n=== ANALYSE DE TOUTES LES OFFRES (factorisée) ===")
            print(f"URL: {parc_url}")
            response = self.session.get(parc_url)
            response.raise_for_status()
            html = response.content
            all_offers = self.extract_all_offers(html)
            print(f"Total des offres trouvées: {len(all_offers)}")
            return {
                'offers': all_offers,
                'success': True
            }
        except Exception as e:
            print(f"Erreur lors de l'analyse exhaustive: {str(e)}")
            return {
                'offers': [],
                'success': False,
                'error': str(e)
            }

def group_offers_by_typology(offers):
    """
    Regroupe une liste d'offres par typologie (restaurants, supermarches, forfaits, services).
    Retourne un dict { 'restaurants': [...], 'supermarches': [...], 'forfaits': [...], 'services': [...] }
    """
    result = {
        'restaurants': [],
        'supermarches': [],
        'forfaits': [],
        'services': []
    }
    for offer in offers:
        if offer['type'] == 'restaurant':
            result['restaurants'].append(offer)
        elif offer['type'] == 'supermarche':
            result['supermarches'].append(offer)
        elif offer['type'] == 'forfait':
            result['forfaits'].append(offer)
        elif offer['type'] == 'service':
            result['services'].append(offer)
    return result

# --- Exemple d'intégration dans une route Flask (API) ---
# from flask import Flask, request, jsonify
# app = Flask(__name__)
#
# @app.route('/api/offers')
# def api_offers():
#     parc_url = request.args.get('url')
#     service = RestaurantService()
#     result = service.get_all_offers(parc_url)
#     if result['success']:
#         grouped = group_offers_by_typology(result['offers'])
#         return jsonify({'success': True, 'offers': grouped})
#     else:
#         return jsonify({'success': False, 'error': result['error']})

# --- Exemple de test simple ---
# def test_extraction():
#     service = RestaurantService()
#     parc_url = "https://www.centerparcs.fr/fr-fr/france/fp_LA_vacances-le-lac-d-ailette/restaurant"
#     result = service.get_all_offers(parc_url)
#     assert result['success']
#     grouped = group_offers_by_typology(result['offers'])
#     assert isinstance(grouped['restaurants'], list)
#     print("Test extraction OK, restaurants trouvés:", len(grouped['restaurants']))

if __name__ == '__main__':
    service = RestaurantService()
    parc_url = "https://www.centerparcs.fr/fr-fr/france/fp_LA_vacances-le-lac-d-ailette/restaurant"
    result = service.get_all_offers(parc_url)
    if result['success']:
        grouped = group_offers_by_typology(result['offers'])
        print("\n=== Résumé par typologie ===")
        for typ, items in grouped.items():
            print(f"\n--- {typ.capitalize()} ({len(items)}) ---")
            for offer in items:
                print(f"[{offer['type']}] {offer['name']}")
                print(f"  Description : {offer['description'][:120]}{'...' if len(offer['description']) > 120 else ''}")
                print(f"  Images : {offer['images'][:2]}")
                print(f"  Type/cuisine : {offer['cuisine_type']}")
                print(f"  Horaires : {offer['horaires']}")
                print(f"  Lien menu : {offer['link']}")
                print(f"  Photo ok : {offer['has_photos']}")
                print()
    else:
        print("Erreur :", result['error']) 