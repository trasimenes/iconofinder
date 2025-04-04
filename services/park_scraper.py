import requests
from bs4 import BeautifulSoup
from typing import Dict, List

class ParkScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @staticmethod
    def extract_base_urls(html_content: str) -> Dict[str, Dict[str, str]]:
        """
        Extrait les URLs de base de tous les parcs à partir du HTML de la carte
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        parks_by_country = {}
        current_country = None

        for item in soup.find_all(['li']):
            # Détecter le pays
            country_group = item.get('class', [])
            if 'group-FR' in country_group:
                current_country = "France"
            elif 'group-BE' in country_group:
                current_country = "Belgique"
            elif 'group-NL' in country_group:
                current_country = "Pays-Bas"
            elif 'group-DE' in country_group:
                current_country = "Allemagne"
            elif 'group-DK' in country_group:
                current_country = "Danemark"

            # Extraire les informations du parc
            popup = item.find('div', class_='pinInformation-popup')
            if popup:
                park_name = popup.find('p', class_='pinInformation-popup--park').text.strip()
                discover_link = popup.find('a', class_='js-Tracking--link')
                if discover_link and current_country:
                    if current_country not in parks_by_country:
                        parks_by_country[current_country] = {}
                    parks_by_country[current_country][park_name] = discover_link['href']

        return parks_by_country

    def get_park_urls(self, park_homepage: str) -> Dict[str, str]:
        """
        Scrape all navigation URLs from a park's homepage
        """
        try:
            response = self.session.get(park_homepage)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver le menu de navigation
            nav_menu = soup.find('ul', class_='submenu-navigation')
            if not nav_menu:
                return {}

            urls = {}
            for item in nav_menu.find_all('li', class_='submenu-navItem'):
                link = item.find('a')
                if not link:
                    continue
                
                # Extraire le texte et l'URL
                text = link.text.strip()
                url = link.get('href', '')
                
                # Mapper le texte français vers nos clés en anglais
                key_mapping = {
                    'Le domaine': 'domain',
                    'Hébergements': 'cottages',
                    'Activités': 'activities',
                    'Restauration': 'restaurants',
                    'Aux alentours': 'surroundings',
                    'Infos pratiques': 'practical_info',
                    'Billets journée': 'day_tickets',
                    'Meetings & Events': 'business'
                }
                
                key = key_mapping.get(text)
                if key and url:
                    urls[key] = url

            return urls
        except Exception as e:
            print(f"Erreur lors du scraping de {park_homepage}: {str(e)}")
            return {} 