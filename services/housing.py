import requests
from bs4 import BeautifulSoup

class HousingService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_housings_with_placeholders(self, parc_url):
        """
        Récupère les hébergements et vérifie leurs photos
        """
        try:
            print(f"\n=== ANALYSE DES HÉBERGEMENTS ===")
            print(f"URL: {parc_url}")
            
            response = self.session.get(parc_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher tous les blocs d'hébergements avec la classe accCart
            housing_blocks = soup.find_all('div', class_='accCart')
            total_housings = len(housing_blocks)
            print(f"\nTotal des hébergements trouvés: {total_housings}")
            
            # Liste pour stocker les hébergements
            all_housings = []
            
            # Pour chaque bloc d'hébergement
            for block in housing_blocks:
                # Récupérer l'ID du cottage (ex: VN1037)
                cottage_id = block.get('id', '').replace('accCart_', '')
                
                # Chercher le titre dans h2.accCart-housingTitle
                title_element = block.find('h2', class_='accCart-housingTitle')
                housing_name = title_element.text.strip() if title_element else f"Cottage {cottage_id}"
                
                print(f"\n=== Analyse de: {housing_name} (ID: {cottage_id}) ===")
                
                # Élargir la recherche avec plusieurs sélecteurs
                slider_pictures = []
                
                # 1. Chercher les images dans sliderPhotos-picture
                slider_container = block.find('div', class_='sliderPhotos')
                if slider_container:
                    slider_pictures = slider_container.find_all('div', class_='sliderPhotos-picture')
                
                # Si rien trouvé, chercher avec un sélecteur alternatif
                if not slider_pictures:
                    slider_pictures = block.find_all('div', class_='sliderPhotos-picture')
                
                # Si toujours rien, essayer de trouver des images directement
                if not slider_pictures:
                    print("Tentative de recherche directe d'images...")
                    direct_images = block.find_all('img', class_='sliderPhotos-img')
                    # Créer des containers virtuels pour les images trouvées directement
                    for img in direct_images:
                        # Créer un container virtuel
                        virtual_container = soup.new_tag('div')
                        virtual_container['class'] = 'sliderPhotos-picture'
                        virtual_container.append(img)
                        slider_pictures.append(virtual_container)
                
                print(f"Conteneurs d'images trouvés: {len(slider_pictures)}")
                
                # Chercher toutes les balises img dans ces conteneurs
                all_images = []
                for picture in slider_pictures:
                    img = picture.find('img')
                    if img:
                        all_images.append(img)
                
                # Si toujours rien, chercher des images n'importe où dans le bloc
                if not all_images:
                    print("Tentative de recherche d'images partout dans le bloc...")
                    all_images = block.find_all('img')
                
                print(f"Images trouvées: {len(all_images)}")
                
                # Détails de chaque image trouvée
                has_photos = False  # Par défaut, on suppose qu'il n'y a pas de photos
                images_details = []
                
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
                            is_valid = True
                            has_photos = True
                    
                    # Vérifier src
                    if not is_valid and src and "default" not in src.lower():
                        if "photos.centerparcs.com" in src or "fp2/photos" in src:
                            is_valid = True
                            has_photos = True
                    
                    # Vérifier data-url-desktop
                    if not is_valid and data_url_desktop and "default" not in data_url_desktop.lower():
                        if "photos.centerparcs.com" in data_url_desktop or "fp2/photos" in data_url_desktop:
                            is_valid = True
                            has_photos = True
                    
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
                
                # Créer l'entrée pour ce cottage
                cottage_entry = {
                    "name": housing_name,
                    "cottage_id": cottage_id,
                    "images_found": len(all_images),
                    "containers_found": len(slider_pictures),
                    "has_photos": has_photos,  # True si au moins une image valide a été trouvée
                    "images_details": images_details  # Stocker les détails pour TOUS les cottages
                }
                
                all_housings.append(cottage_entry)
                
                # Afficher le résultat pour ce cottage
                print(f"Résultat pour {housing_name}: {'Photos OK ✅' if has_photos else 'Photos manquantes ❌'}")
            
            # Trier la liste des hébergements
            all_housings.sort(key=lambda x: x["name"])
            
            # Obtenir la liste des cottages sans photos
            no_photo_cottages = [h for h in all_housings if not h.get("has_photos", False)]
            
            print("\n=== DÉTAILS DES HÉBERGEMENTS SANS PHOTOS ===")
            for housing in no_photo_cottages:
                print(f"\n{housing['name']} (ID: {housing['cottage_id']}):")
                print(f"- Images trouvées: {housing['images_found']}")
                print(f"- Conteneurs d'images trouvés: {housing['containers_found']}")
                if housing.get('images_details'):
                    print("- Détails des images:")
                    for img in housing['images_details']:
                        print(f"\n  src: {img['src']}")
                        print(f"  data-src: {img['data_src']}")
                        print(f"  data-url-desktop: {img['data_url_desktop']}")
                        print(f"  Valide: {'✓ (vraie photo)' if img['is_valid'] else '✗ (placeholder ou non trouvée)'}")
                else:
                    print("- Aucune image trouvée")
            
            print(f"\n=== RÉSUMÉ ===")
            print(f"Total des hébergements: {total_housings}")
            print(f"Hébergements analysés: {total_housings}")
            print(f"Hébergements avec vraies photos: {len(all_housings) - len(no_photo_cottages)}")
            print(f"Hébergements avec photos manquantes/placeholders: {len(no_photo_cottages)}")
            
            return {
                "housings": all_housings
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