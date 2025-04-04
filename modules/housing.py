import requests
from bs4 import BeautifulSoup

def get_missing_housing_photos(url):
    """
    Scrape la page des hébergements Center Parcs et identifie les logements avec ou sans photos.
    """
    try:
        print("\n🟢 Scrap housing lancé :", url)

        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        cottages = []

        # Cibler chaque logement
        cottage_blocks = soup.select("div.accCart")
        print(f"🔍 Nombre de cottages trouvés : {len(cottage_blocks)}")

        for block in cottage_blocks:
            # Nom du logement
            name_tag = block.select_one("h2.accCart-housingTitle") or \
                       block.select_one("h3") or block.select_one("h4") or \
                       block.select_one("strong") or block.select_one("p")
            name = name_tag.get_text(strip=True) if name_tag else block.get("id", "Sans nom")

            # Récupération des images du slider
            image_tags = block.select("div.sliderPhotos-slide img")
            image_urls = []
            for img in image_tags:
                image_url = img.get("data-src") or img.get("src")
                if image_url:
                    print(f"📸 Image trouvée pour {name} :", image_url)
                    image_urls.append(image_url)

            # Vérifie les images valides
            valid_images = [
                url for url in image_urls
                if not url.endswith("default/500x375.jpg")
            ]

            cottages.append({
                "name": name,
                "missing": [] if valid_images else ["image manquante"]
            })

        return cottages

    except Exception as e:
        print(f"[ERREUR SCRAPING HOUSING] {e}")
        return []
