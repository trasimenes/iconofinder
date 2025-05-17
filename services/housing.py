import requests
from bs4 import BeautifulSoup
from config.urls import PARKS_URLS
import re

class HousingService:
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

    def get_housings_with_placeholders(self, parc_url):
        """
        Récupère les hébergements et vérifie leurs photos
        """
        try:
            print(f"\n=== ANALYSE DES HÉBERGEMENTS ===")
            print(f"URL: {parc_url}")
            
            response = self.session.get(parc_url)
            response.raise_for_status()
            
            print("\n=== HEADERS DE LA RÉPONSE ===")
            for key, value in response.headers.items():
                print(f"{key}: {value}")
            
            print("\n=== DÉBUT DU HTML ===")
            print(response.text[:1000])  # Affiche les 1000 premiers caractères
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher tous les blocs d'hébergements avec différents sélecteurs
            housing_blocks = []
            selectors = [
                'div.accCart',  # Sélecteur original
                'div[class*="cottage"]',  # Tout div contenant "cottage" dans sa classe
                'div[class*="housing"]',  # Tout div contenant "housing" dans sa classe
                'div[class*="accommodation"]'  # Tout div contenant "accommodation" dans sa classe
            ]
            
            for selector in selectors:
                blocks = soup.select(selector)
                if blocks:
                    print(f"Trouvé {len(blocks)} hébergements avec le sélecteur: {selector}")
                    housing_blocks.extend(blocks)
            
            # Dédupliquer les blocs en utilisant le nom de l'hébergement
            unique_blocks = []
            seen_names = set()
            
            for block in housing_blocks:
                # On ignore maintenant si le parent a la classe u-Hidden : on prend tout !
                title_selectors = [
                    'h2.accCart-housingTitle',
                    'h2[class*="title"]',
                    'h3[class*="title"]',
                    '.cottage-name',
                    '.housing-name'
                ]
                
                title_element = None
                for selector in title_selectors:
                    title_element = block.select_one(selector)
                    if title_element:
                        break
                
                housing_name = title_element.text.strip() if title_element else None
                cottage_id = block.get('id', '').replace('accCart_', '')
                unique_key = f"{housing_name}_{cottage_id}"
                if housing_name and unique_key not in seen_names:
                    seen_names.add(unique_key)
                    unique_blocks.append(block)
            
            housing_blocks = unique_blocks
            total_housings = len(housing_blocks)
            print(f"\nTotal des hébergements uniques trouvés: {total_housings}")
            
            # Liste pour stocker les hébergements
            all_housings = []
            
            # Pour chaque bloc d'hébergement
            for block in housing_blocks:
                # Récupérer l'ID du cottage
                cottage_id = block.get('id', '').replace('accCart_', '')
                
                # Chercher le titre (on l'a déjà trouvé plus haut)
                title_element = None
                for selector in title_selectors:
                    title_element = block.select_one(selector)
                    if title_element:
                        break
                
                housing_name = title_element.text.strip() if title_element else f"Hébergement {cottage_id}"
                
                print(f"\n=== Analyse de: {housing_name} (ID: {cottage_id}) ===")
                
                # Chercher les images avec différents sélecteurs
                image_selectors = [
                    'img.sliderPhotos-img',
                    'img[class*="cottage"]',
                    'img[class*="housing"]',
                    'img[data-src*="photos"]',
                    'img[src*="photos"]'
                ]
                
                all_images = []
                for selector in image_selectors:
                    images = block.select(selector)
                    if images:
                        print(f"Trouvé {len(images)} images avec le sélecteur: {selector}")
                        all_images.extend(images)
                
                # Dédupliquer les images
                unique_images = []
                seen_srcs = set()
                
                for img in all_images:
                    src = img.get('src', '')
                    data_src = img.get('data-src', '')
                    key = f"{src}|{data_src}"
                    
                    if key not in seen_srcs:
                        seen_srcs.add(key)
                        unique_images.append(img)
                
                all_images = unique_images
                print(f"Images uniques trouvées: {len(all_images)}")
                
                # Détails de chaque image trouvée
                has_photos = False
                images_details = []
                
                # Analyse des images trouvées
                for img in all_images:
                    src = img.get('src', '')
                    data_src = img.get('data-src', '')
                    data_url_desktop = img.get('data-url-desktop', '')
                    
                    # Une image est valide si elle a une URL et ne contient pas "default" ou "placeholder"
                    is_valid = False
                    
                    # Vérifier les différentes sources d'URL
                    for url in [data_src, src, data_url_desktop]:
                        if url and not any(invalid in url.lower() for invalid in ['default', 'placeholder', 'blank']):
                            if any(valid in url for valid in ['photos.centerparcs.com', 'fp2/photos']):
                                is_valid = True
                                has_photos = True
                                break
                    
                    details = {
                        'cottage_id': cottage_id,
                        'src': src,
                        'data_src': data_src,
                        'data_url_desktop': data_url_desktop,
                        'is_valid': is_valid
                    }
                    images_details.append(details)
                    
                    print(f"\nImage trouvée:")
                    print(f"- ID du cottage: {cottage_id}")
                    print(f"- src: {src}")
                    print(f"- data-src: {data_src}")
                    print(f"- data-url-desktop: {data_url_desktop}")
                    print(f"- Valide: {'✓ (vraie photo)' if is_valid else '✗ (placeholder ou non trouvée)'}")
                
                # Déterminer la première vraie photo trouvée (pour le champ image_src)
                image_src = ''
                for img in all_images:
                    for url in [img.get('data-src', ''), img.get('src', ''), img.get('data-url-desktop', '')]:
                        if url and not any(invalid in url.lower() for invalid in ['default', 'placeholder', 'blank']):
                            if any(valid in url for valid in ['photos.centerparcs.com', 'fp2/photos']):
                                image_src = url
                                break
                    if image_src:
                        break
                
                # Extraction ultra-fiable de la capacité
                capacity = "?"
                found_capacity = False
                # 1. Cibler le <li> avec l'icône couple
                for item in block.select('ul.accCart-specifications li.accCart-specificationsItem'):
                    print("[DEBUG] LI trouvé :", item.prettify())
                    if item.select_one('i.icon-couple'):
                        txt = item.select_one('span.textIcon')
                        if txt:
                            value = txt.get_text()
                            print(f"[DEBUG] Texte brut dans span.textIcon (icône couple) : '{value}'")
                            value_clean = value.replace('\n', ' ').replace('\r', ' ').strip()
                            print(f"[DEBUG] Texte nettoyé : '{value_clean}'")
                            match = re.search(r"(\d+)\s*(pers\.?|personnes?)", value_clean, re.IGNORECASE)
                            if match:
                                capacity = match.group(1)
                                found_capacity = True
                                break
                # 2. Recherche récursive dans tout le bloc si non trouvé
                if not found_capacity:
                    for span in block.find_all(string=True, recursive=True):
                        txt = span.strip()
                        match = re.search(r"(\d+)\s*(pers\.?|personnes?)", txt, re.IGNORECASE)
                        if match:
                            capacity = match.group(1)
                            found_capacity = True
                            break
                # 3. Fallbacks attributs data-* si rien trouvé
                if not found_capacity:
                    attrs_to_try = [
                        'data-maxcapacity', 'data-housingname', 'data-cottagename', 'data-housing', 'data-housingcode', 'data-name'
                    ]
                    for attr in attrs_to_try:
                        val = block.get(attr, '')
                        if val:
                            match = re.search(r"(\d+)", val)
                            if match:
                                capacity = match.group(1)
                                found_capacity = True
                                break
                    if not found_capacity:
                        for btn in block.select('a, button'):
                            for attr in attrs_to_try:
                                val = btn.get(attr, '')
                                if val:
                                    match = re.search(r"(\d+)", val)
                                    if match:
                                        capacity = match.group(1)
                                        found_capacity = True
                                        break
                            if found_capacity:
                                break
                if not found_capacity:
                    print("[DEBUG] Bloc sans capacité trouvée :\n", block.prettify())
                # Extraction du type depuis le nom (à faire après la capacité)
                type_match = re.search(r'(VIP|Premium|Comfort|Exclusive|Standard|Hotel)', housing_name, re.IGNORECASE)
                if type_match:
                    cottage_type = type_match.group(1)
                elif "Maison dans les Arbres" in housing_name:
                    cottage_type = "Maison dans les Arbres"
                elif "Animaux de la Forêt" in housing_name or "Animaux de la forêt" in housing_name:
                    cottage_type = "Animaux de la Forêt"
                elif "Aventure" in housing_name:
                    cottage_type = "Aventure"
                elif "Maison Flottante" in housing_name:
                    cottage_type = "Maison Flottante"
                elif "Merveilles de la Nature" in housing_name:
                    cottage_type = "Merveilles de la Nature"
                elif "Bien-être" in housing_name:
                    cottage_type = "Bien-être"
                elif "Suite d'hôtel" in housing_name or "Suite d'hotel" in housing_name or "Suite d'hôtel" in housing_name:
                    cottage_type = "Suite d'hôtel"
                else:
                    cottage_type = "?"
                # Créer l'entrée pour ce cottage
                cottage_entry = {
                    "name": housing_name,
                    "cottage_id": cottage_id,
                    "type": cottage_type,
                    "capacity": capacity,
                    "images_found": len(all_images),
                    "has_photos": has_photos,
                    "image_src": image_src,
                    "images_details": images_details
                }
                
                all_housings.append(cottage_entry)
                
                # Afficher le résultat pour ce cottage
                print(f"Résultat pour {housing_name}: {'Photos OK ✅' if has_photos else 'Photos manquantes ❌'}")
                print(f"- Capacité extraite : {capacity} personnes")
            
            # Trier la liste des hébergements
            all_housings.sort(key=lambda x: x["name"])
            
            # Obtenir la liste des cottages sans photos
            no_photo_cottages = [h for h in all_housings if not h.get("has_photos", False)]
            
            print("\n=== RÉSUMÉ ===")
            print(f"Total des hébergements: {total_housings}")
            print(f"Hébergements avec vraies photos: {len(all_housings) - len(no_photo_cottages)}")
            print(f"Hébergements avec photos manquantes: {len(no_photo_cottages)}")
            
            return {
                "housings": all_housings,
                "no_missing_photos": len(no_photo_cottages) == 0
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "housings": []
            }

    def get_missing_housing_photos(self, cottage_url):
        """
        Cette méthode est dépréciée en faveur de get_housings_with_placeholders
        """
        print("Cette méthode est dépréciée. Utilisez get_housings_with_placeholders à la place.")
        return [] 