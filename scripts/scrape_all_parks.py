import os
from services.park_scraper import ParkScraper

def main():
    print("Mise à jour des URLs des parcs...")
    
    # Créer le dossier config s'il n'existe pas
    os.makedirs('config', exist_ok=True)
    
    # Lire le contenu du fichier map.html
    with open('map.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Initialiser le scraper
    scraper = ParkScraper()
    
    # Extraire les URLs de base des parcs
    parks_by_country = scraper.extract_base_urls(html_content)
    
    # Scraper les URLs de navigation pour chaque parc
    all_parks_urls = {}
    for country, parks in parks_by_country.items():
        all_parks_urls[country] = {}
        for park_name, base_url in parks.items():
            # Scraper les URLs de navigation
            park_urls = scraper.get_park_urls(base_url)
            if park_urls:
                all_parks_urls[country][park_name] = park_urls
            else:
                # En cas d'échec du scraping, utiliser l'URL de base
                all_parks_urls[country][park_name] = {'base_url': base_url}
    
    # Générer le fichier de configuration Python
    with open('config/urls.py', 'w', encoding='utf-8') as f:
        f.write('# Configuration des URLs des parcs Center Parcs\n\n')
        f.write('PARKS_URLS = {\n')
        for country, parks in all_parks_urls.items():
            f.write(f'    "{country}": {{\n')
            for park_name, urls in parks.items():
                f.write(f'        "{park_name}": {{\n')
                for key, url in urls.items():
                    f.write(f'            "{key}": "{url}",\n')
                f.write('        },\n')
            f.write('    },\n')
        f.write('}\n')
    
    print("Terminé !")

if __name__ == '__main__':
    main() 