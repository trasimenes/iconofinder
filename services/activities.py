import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import numpy as np

class ActivityService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def is_placeholder_image(self, img_url):
        """
        Vérifie si une image est un placeholder en vérifiant si 'default' est dans l'URL
        """
        return 'default' in img_url.lower() if img_url else True

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
            
            # Chercher tous les blocs d'activités
            activity_blocks = soup.find_all(['a', 'div'], class_=['js_activityBlock', 'activity-item', 'activity-card'])
            print(f"\nBlocs d'activités trouvés: {len(activity_blocks)}")
            
            # Liste pour stocker les activités avec photos manquantes
            activities_with_placeholders = []
            no_missing_photos = True
            
            for block in activity_blocks:
                # Chercher l'image
                img = block.find('img', class_=['lazy', 'activity-image'])
                if not img:
                    continue
                
                # Récupérer le titre de l'activité - essayer plusieurs sélecteurs
                title = None
                # 1. Essayer les sélecteurs de classe spécifiques
                title = block.find(['h2', 'h3', 'h4', 'span', 'p'], 
                                class_=['activity-title', 'activity-name', 'h4-like', 'title'])
                
                # 2. Si pas trouvé, chercher dans le texte alt de l'image
                if not title and img.get('alt'):
                    title = type('Title', (), {'text': img.get('alt')})()
                
                # 3. Si toujours pas trouvé, chercher n'importe quel texte dans le bloc
                if not title:
                    text_content = block.get_text(strip=True)
                    if text_content:
                        title = type('Title', (), {'text': text_content})()
                
                activity_name = title.text.strip() if title else "Activité sans nom"
                
                # Vérifier les différentes sources d'images possibles
                src = img.get('src', '')
                data_src = img.get('data-src', '')
                data_url_desktop = img.get('data-url-desktop', '')
                
                # Une image est considérée comme manquante si:
                # 1. Elle n'a pas de source du tout
                # 2. Elle utilise une image par défaut
                # 3. Elle a une source vide
                is_missing = False
                
                if not (src or data_src or data_url_desktop):
                    is_missing = True
                elif all(('default' in url.lower() if url else True) for url in [src, data_src, data_url_desktop]):
                    is_missing = True
                elif all(url == '' for url in [src, data_src, data_url_desktop]):
                    is_missing = True
                
                if is_missing:
                    no_missing_photos = False
                    activities_with_placeholders.append({
                        'name': activity_name,
                        'image_src': src or data_src or data_url_desktop or "Pas d'URL d'image"
                    })
                    print("\nActivité avec image manquante trouvée:")
                    print(f"- Nom: {activity_name}")
                    print(f"- URL de l'image: {src or data_src or data_url_desktop or 'Pas d URL'}")
            
            return {
                'activities': activities_with_placeholders,
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

    def get_housings_with_placeholders(self, parc_url):
        """
        Récupère les hébergements qui ont des images manquantes
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
                
                # Chercher les images dans sliderPhotos-picture
                slider_pictures = block.find_all('div', class_='sliderPhotos-picture')
                print(f"Conteneurs d'images trouvés: {len(slider_pictures)}")
                
                # Chercher toutes les balises img dans ces conteneurs
                all_images = []
                for picture in slider_pictures:
                    img = picture.find('img')
                    if img:
                        all_images.append(img)
                
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
                    "has_photos": has_photos  # True si au moins une image valide a été trouvée
                }
                
                # Ajouter les détails des images seulement pour les cottages sans photos
                if not has_photos:
                    cottage_entry["images_details"] = images_details
                
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
                "no_missing_photos": len(no_photo_cottages) == 0,
                "housings": all_housings,
                "details": no_photo_cottages
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "housings": [],
                "details": []
            }
