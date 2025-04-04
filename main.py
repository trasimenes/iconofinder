import os
from flask import Flask, render_template, request, session, redirect, url_for
<<<<<<< HEAD
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

# Clé secrète pour les sessions
app.secret_key = "/Xfn,MN~s}.;q1M1'Om`YD;x_-<ACZ"

# Charger les traductions
def load_translations():
    with open("translations/translations.json", "r", encoding="utf-8") as file:
        return json.load(file)

translations = load_translations()

# Données des parcs par pays
parcs = {
    "France": {
        "Villages Nature Paris": "https://www.centerparcs.fr/fr-fr/france/fp_VN_vacances-domaine-villages-nature-paris/toutes-les-activites",
        "Le Lac d'Ailette": "https://www.centerparcs.fr/fr-fr/france/fp_LA_vacances-domaine-le-lac-d-ailette/toutes-les-activites",
        "Les Hauts de Bruyères": "https://www.centerparcs.fr/fr-fr/france/fp_CH_vacances-domaine-les-hauts-de-bruyeres/toutes-les-activites",
        "Le Bois aux Daims": "https://www.centerparcs.fr/fr-fr/france/fp_BD_vacances-domaine-le-bois-aux-daims/toutes-les-activites",
        "Les Bois-Francs": "https://www.centerparcs.fr/fr-fr/france/fp_BF_vacances-domaine-les-bois-francs/toutes-les-activites",
        "Les Trois Forêts": "https://www.centerparcs.fr/fr-fr/france/fp_TF_vacances-domaine-les-trois-forets/toutes-les-activites",
        "Les Landes de Gascogne": "https://www.centerparcs.fr/fr-fr/france/fp_LG_vacances-domaine-les-landes-de-gascogne/toutes-les-activites"
    },
    "Belgique": {
        "Park De Haan": "https://www.centerparcs.fr/fr-fr/belgique/fp_HA_vacances-domaine-park-de-haan/toutes-les-activites",
        "Les Ardennes": "https://www.centerparcs.fr/fr-fr/belgique/fp_AR_vacances-domaine-les-ardennes/toutes-les-activites",
        "Erperheide": "https://www.centerparcs.fr/fr-fr/belgique/fp_EP_vacances-domaine-erperheide/toutes-les-activites",
        "Terhills Resort": "https://www.centerparcs.fr/fr-fr/belgique/fp_TH_vacances-domaine-terhills-resort/toutes-les-activites",
        "De Vossemeren": "https://www.centerparcs.fr/fr-fr/belgique/fp_VM_vacances-domaine-de-vossemeren/toutes-les-activites"
    },
    "Pays-Bas": {
        "De Eemhof": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_EH_vacances-domaine-de-eemhof/toutes-les-activites",
        "Port Zélande": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_PZ_vacances-domaine-port-zelande/toutes-les-activites",
        "Parc Sandur": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_SR_vacances-domaine-parc-sandur/toutes-les-activites",
        "Limburgse Peel": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_LH_vacances-domaine-limburgse-peel/toutes-les-activites",
        "Het Heijderbos": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_HB_vacances-domaine-het-heijderbos/toutes-les-activites",
        "Park Zandvoort": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_ZV_vacances-domaine-park-zandvoort/toutes-les-activites",
        "Het Meerdal": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_MD_vacances-domaine-het-meerdal/toutes-les-activites",
        "De Huttenheugte": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_HH_vacances-domaine-de-huttenheugte/toutes-les-activites",
        "De Kempervennen": "https://www.centerparcs.fr/fr-fr/pays-bas/fp_KV_vacances-domaine-de-kempervennen/toutes-les-activites"
    },
    "Allemagne": {
        "Park Bostalsee": "https://www.centerparcs.fr/fr-fr/allemagne/fp_BT_vacances-domaine-park-bostalsee/toutes-les-activites",
        "Park Allgäu": "https://www.centerparcs.fr/fr-fr/allemagne/fp_AG_vacances-domaine-park-allgau/toutes-les-activites",
        "Park Nordseeküste": "https://www.centerparcs.fr/fr-fr/allemagne/fp_BK_vacances-domaine-park-nordseekuste/toutes-les-activites",
        "Bispinger Heide": "https://www.centerparcs.fr/fr-fr/allemagne/fp_BS_vacances-domaine-bispinger-heide/toutes-les-activites",
        "Park Hochsauerland": "https://www.centerparcs.fr/fr-fr/allemagne/fp_SL_vacances-domaine-park-hochsauerland/toutes-les-activites",
        "Park Eifel": "https://www.centerparcs.fr/fr-fr/allemagne/fp_HE_vacances-domaine-park-eifel/toutes-les-activites"
    },
    "Danemark": {
        "Nordborg Resort": "https://www.centerparcs.fr/fr-fr/danemark/fp_NO_vacances-domaine-nordborg-resort/toutes-les-activites"
    }
}

# Fonction pour récupérer la traduction selon la langue active
def get_translation(key):
    lang = session.get("lang", "fr")  # Par défaut, français
    return translations.get(lang, {}).get(key, key)  # Retourne la clé si elle n'est pas trouvée

# Route pour changer la langue
@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in translations:
        session["lang"] = lang  # Stocke la langue sélectionnée dans la session
    return redirect(request.referrer or url_for("home"))  # Recharge la page précédente ou renvoie à la page d'accueil

=======
from config.urls import PARKS_URLS
from services.activities import ActivityService
from services.housing import HousingService
from utils.translations import load_translations, get_translation, translations

app = Flask(__name__)
app.secret_key = "/Xfn,MN~s}.;q1M1'Om`YD;x_-<ACZ"

print("=== FLASK SERVEUR EN TRAIN DE DÉMARRER ===")

# Initialisation des services
activity_service = ActivityService()
housing_service = HousingService()

def search_activities(country, parc):
    """Recherche les activités avec photos manquantes"""
    print("\n=== RECHERCHE D'ACTIVITÉS ===")
    print(f"Pays: {country}")
    print(f"Parc: {parc}")
    
    final_results = {}
    countries_to_process = [country] if country != "Tous" else PARKS_URLS.keys()

    for current_country in countries_to_process:
        if parc == "Tous":
            print(f"\nRecherche pour tous les parcs de {current_country}:")
            # Traiter tous les parcs du pays sélectionné
            all_parks_results = {}
            for park_name, park_urls in PARKS_URLS.get(current_country, {}).items():
                activities_url = park_urls.get("activities")
                if activities_url:
                    print(f"🔍 Recherche dans {park_name}: {activities_url}")
                    activities = activity_service.get_activities_with_placeholders(activities_url)
                    activities["url"] = activities_url
                    # Ajouter le parc même s'il n'a pas d'activités avec photos manquantes
                    all_parks_results[park_name] = activities
            
            if all_parks_results:  # Si on a trouvé au moins un parc
                final_results[current_country] = all_parks_results
        else:
            activities_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("activities")
            if activities_url:
                print(f"\nRecherche pour {parc} dans {current_country}:")
                print(f"🔍 URL: {activities_url}")
                activities = activity_service.get_activities_with_placeholders(activities_url)
                activities["url"] = activities_url
                # Ajouter le parc même s'il n'a pas d'activités avec photos manquantes
                final_results[current_country] = {parc: activities}
    
    return final_results

def search_housings(country, parc):
    """Recherche les hébergements avec photos manquantes"""
    print("\n=== RECHERCHE D'HÉBERGEMENTS ===")
    print(f"Pays: {country}")
    print(f"Parc: {parc}")
    
    final_results = {}
    countries_to_process = [country] if country != "Tous" else PARKS_URLS.keys()

    for current_country in countries_to_process:
        if parc == "Tous":
            print(f"\nRecherche pour tous les parcs de {current_country}:")
            # Traiter tous les parcs du pays sélectionné
            all_parks_results = {}
            for park_name, park_urls in PARKS_URLS.get(current_country, {}).items():
                cottages_url = park_urls.get("cottages")
                if cottages_url:
                    print(f"🏠 Recherche dans {park_name}: {cottages_url}")
                    result = housing_service.get_housings_with_placeholders(cottages_url)
                    result["url"] = cottages_url
                    # Ajouter le parc même s'il n'a pas d'hébergements avec photos manquantes
                    all_parks_results[park_name] = result
            
            if all_parks_results:  # Si on a trouvé au moins un parc
                final_results[current_country] = all_parks_results
        else:
            cottages_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("cottages")
            if cottages_url:
                print(f"\nRecherche pour {parc} dans {current_country}:")
                print(f"🏠 URL: {cottages_url}")
                result = housing_service.get_housings_with_placeholders(cottages_url)
                result["url"] = cottages_url
                # Ajouter le parc même s'il n'a pas d'hébergements avec photos manquantes
                final_results[current_country] = {parc: result}
    
    return final_results

def format_park_name(name):
    """
    Formate le nom du parc pour l'URL :
    - Cas spécial pour Villages Nature Paris qui utilise VN
    - Pour les autres, remplace les espaces par des _
    """
    if name == "Villages Nature Paris":
        return "VN"
    return name.replace(' ', '_')

# Routes
@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in translations:
        session["lang"] = lang
    return redirect(request.referrer or url_for("home"))
>>>>>>> temp-branch

@app.route('/')
def home():
    return render_template('home.html', translate=get_translation)

<<<<<<< HEAD
    

@app.route('/recherche')
def recherche():
    return render_template('search.html', parcs=parcs, t=get_translation)

@app.route('/results', methods=['GET'])
def results():
    country = request.args.get('country')
    parc = request.args.get('parc')

    if not country or not parc:
        return get_translation("error_missing_params")

    final_results = {}

    if country == "Tous" and parc == "Tous":
        for country_name, parks in parcs.items():
            final_results[country_name] = {}
            for parc_name, parc_url in parks.items():
                activities = get_activities_with_placeholders(parc_url)
                final_results[country_name][parc_name] = activities

    elif parc == "Tous":
        if country in parcs:
            final_results[country] = {}
            for parc_name, parc_url in parcs[country].items():
                activities = get_activities_with_placeholders(parc_url)
                final_results[country][parc_name] = activities

    else:
        parc_url = parcs.get(country, {}).get(parc)
        if not parc_url:
            return get_translation("error_invalid_park_url")

        activities = get_activities_with_placeholders(parc_url)
        final_results[country] = {parc: activities}

    return render_template('results.html', results=final_results, translate=get_translation)

# Fonction pour scraper les activités avec placeholders
def get_activities_with_placeholders(parc_url):
    placeholder_base_url = "https://static.centerparcs.com/"
    placeholder_image_suffix = "/assets/images/default/500x375.jpg"

    try:
        response = requests.get(parc_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        activity_blocks = soup.find_all('a', class_='js-Tracking--link')
        activities_with_placeholder = [
            activity.find('p', class_='h4-like').text.strip()
            for activity in activity_blocks
            if any(
                img.get('src', '').startswith(placeholder_base_url) and
                img.get('src', '').endswith(placeholder_image_suffix)
                for img in activity.find_all('img')
            )
        ]
        return activities_with_placeholder if activities_with_placeholder else [get_translation("no_activities_found")]
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        return [get_translation("scraping_error")]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
=======
@app.route('/recherche')
def recherche():
    return render_template('search.html', parcs=PARKS_URLS, t=get_translation)

@app.route('/results')
def results():
    country = request.args.get('country')
    parc = request.args.get('parc')
    search_type = request.args.get('type')
    
    if not all([country, parc, search_type]):
        return render_template('results.html', error="Paramètres manquants", translate=get_translation)

    if search_type == "Activités":
        # Utiliser la fonction search_activities pour gérer tous les cas
        results = search_activities(country, parc)
        if not results:
            return render_template('results.html', 
                                error="URL des activités non trouvée", 
                                translate=get_translation)
        
        return render_template('results.html', 
                            type=search_type,
                            results_by_park=results,
                            translate=get_translation)
    else:
        # Utiliser la fonction search_housings pour gérer tous les cas
        results = search_housings(country, parc)
        if not results:
            return render_template('results.html', 
                                error="URL des hébergements non trouvée", 
                                translate=get_translation)
        
        return render_template('results.html',
                            type=search_type,
                            results_by_park=results,
                            translate=get_translation)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"=== FLASK EN ÉCOUTE SUR http://0.0.0.0:{port} ===")
    app.run(host="0.0.0.0", port=port, debug=True)
>>>>>>> temp-branch
