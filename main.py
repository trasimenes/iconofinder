import os
from flask import Flask, render_template, request, session, redirect, url_for
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

@app.route('/')
def home():
    return render_template('home.html', translate=get_translation)

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
