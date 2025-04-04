import os
from scripts.update_park_urls import main as update_urls

def save_map_html(html_content):
    """Sauvegarde le HTML de la carte dans un fichier"""
    with open('map.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    # Créer les dossiers nécessaires
    os.makedirs('config', exist_ok=True)
    os.makedirs('services', exist_ok=True)
    os.makedirs('scripts', exist_ok=True)

    # Lancer la mise à jour des URLs
    print("Mise à jour des URLs des parcs...")
    update_urls()
    print("Terminé !")

if __name__ == "__main__":
    main() 