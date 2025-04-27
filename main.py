import os
import json
import threading
import time
import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from config.urls import PARKS_URLS
from services.activities import ActivityService
from services.housing import HousingService
from services.restaurants import RestaurantService
from utils.translations import load_translations, get_translation, translations

app = Flask(__name__)
app.secret_key = "/Xfn,MN~s}.;q1M1'Om`YD;x_-<ACZ"

print("=== FLASK SERVEUR EN TRAIN DE DÉMARRER ===")

# Initialisation des services
activity_service = ActivityService()
housing_service = HousingService()
restaurant_service = RestaurantService()

SNAPSHOT_FILE = 'snapshots.json'
PROGRESS_FILE = 'snapshot_progress.json'

def load_snapshots():
    if not os.path.exists(SNAPSHOT_FILE):
        return []
    with open(SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_snapshots(snapshots):
    with open(SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)

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
                    print(f"🎯 Recherche dans {park_name}: {activities_url}")
                    result = activity_service.get_activities_with_placeholders(activities_url)
                    result["url"] = activities_url
                    # Ajouter le parc même s'il n'a pas d'activités avec photos manquantes
                    all_parks_results[park_name] = result
            
            if all_parks_results:  # Si on a trouvé au moins un parc
                final_results[current_country] = all_parks_results
        else:
            activities_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("activities")
            if activities_url:
                print(f"\nRecherche pour {parc} dans {current_country}:")
                print(f"🎯 URL: {activities_url}")
                result = activity_service.get_activities_with_placeholders(activities_url)
                result["url"] = activities_url
                # Ajouter le parc même s'il n'a pas d'activités avec photos manquantes
                final_results[current_country] = {parc: result}
    
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

def search_restaurants(country, parc):
    """Recherche les restaurants avec photos manquantes"""
    print("\n=== RECHERCHE DE RESTAURANTS ===")
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
                restaurants_url = park_urls.get("restaurants")
                if restaurants_url:
                    print(f"🍽️ Recherche dans {park_name}: {restaurants_url}")
                    result = restaurant_service.get_restaurants_with_placeholders(restaurants_url)
                    result["url"] = restaurants_url
                    # Ajouter le parc même s'il n'a pas de restaurants avec photos manquantes
                    all_parks_results[park_name] = result
            
            if all_parks_results:  # Si on a trouvé au moins un parc
                final_results[current_country] = all_parks_results
        else:
            restaurants_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("restaurants")
            if restaurants_url:
                print(f"\nRecherche pour {parc} dans {current_country}:")
                print(f"🍽️ URL: {restaurants_url}")
                result = restaurant_service.get_restaurants_with_placeholders(restaurants_url)
                result["url"] = restaurants_url
                # Ajouter le parc même s'il n'a pas de restaurants avec photos manquantes
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

@app.before_request
def before_request():
    if 'language' not in session:
        session['language'] = 'fr'

@app.route('/')
def home():
    countries = ['Tous'] + sorted(list(PARKS_URLS.keys()))  # Ajoute "Tous" et trie les pays
    return render_template('index.html', countries=countries, translate=get_translation)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang not in ['fr', 'en']:
        return jsonify({'success': False, 'error': 'Invalid language'})
    
    session['language'] = lang
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': True,
            'language': lang,
            'translations': translations[lang]
        })
    
    next_url = request.args.get('next', '/')
    return redirect(next_url)

@app.route('/api/parks')
def get_parks():
    country = request.args.get('country')
    if not country:
        return jsonify({'error': 'Pays non spécifié', 'parks': []})
    
    if country == 'Tous':
        # Pour "Tous", on retourne tous les parcs de tous les pays
        all_parks = []
        for parks in PARKS_URLS.values():
            all_parks.extend(parks.keys())
        return jsonify({'parks': sorted(list(set(all_parks)))})  # Supprime les doublons et trie
    
    if country not in PARKS_URLS:
        return jsonify({'error': 'Pays non valide', 'parks': []})
    
    parks = sorted(list(PARKS_URLS[country].keys()))  # Trie les parcs par ordre alphabétique
    return jsonify({'parks': parks})

@app.route('/recherche')
def recherche():
    return render_template('search.html', parcs=PARKS_URLS, t=get_translation)

@app.route('/api/search')
def api_search():
    """
    Route API pour la recherche asynchrone
    Retourne les résultats pour un pays spécifique
    """
    country = request.args.get('country')
    parc = request.args.get('parc')
    search_type = request.args.get('type')
    
    if not all([country, parc, search_type]):
        return jsonify({'error': 'Paramètres manquants'})

    try:
        if search_type == "Hébergements":
            results = search_housings(country, parc)
        elif search_type == "Activités":
            results = search_activities(country, parc)
        elif search_type == "Restaurants":
            results = search_restaurants(country, parc)
        else:
            return jsonify({'error': 'Type de recherche non valide'})
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/results')
def results():
    country = request.args.get('country')
    parc = request.args.get('parc')
    search_type = request.args.get('type')
    
    if not all([country, parc, search_type]):
        return render_template('results.html', error="Paramètres manquants", translate=get_translation)

    # Préparer la structure des pays à afficher
    countries = ['France']  # On commence toujours par la France
    if country == "Tous":
        # Ajouter les autres pays dans l'ordre souhaité
        other_countries = [c for c in PARKS_URLS.keys() if c != 'France']
        countries.extend(other_countries)
    else:
        countries = [country]

    return render_template('results.html',
                        countries=countries,
                        type=search_type,
                        parc=parc,
                        translate=get_translation)

@app.route('/results_from_snapshot')
def results_from_snapshot():
    country = request.args.get('country')
    parc = request.args.get('parc')
    search_type = request.args.get('type')
    snapshots = load_snapshots()
    if not snapshots:
        return render_template('results.html', error="Aucun snapshot disponible", translate=get_translation)
    last = snapshots[-1]
    data = last['data']
    filtered = {}
    countries = []
    if country == "Tous":
        countries = list(data['activities'].keys())
    else:
        countries = [country]
    for c in countries:
        filtered[c] = {}
        if parc == "Tous":
            parcs = data['activities'][c].keys()
        else:
            parcs = [parc]
        for p in parcs:
            if search_type == "Activités":
                filtered[c][p] = data['activities'][c].get(p, {})
            elif search_type == "Hébergements":
                filtered[c][p] = data['housings'][c].get(p, {})
            elif search_type == "Restaurants":
                filtered[c][p] = data['restaurants'][c].get(p, {})
    return render_template('results.html', countries=countries, type=search_type, parc=parc, results=filtered, translate=get_translation)

def get_current_language():
    """
    Retourne la langue actuelle, avec 'fr' comme langue par défaut
    """
    return session.get('language', 'fr')

# Assurez-vous que la fonction get_translation est disponible dans tous les templates
@app.context_processor
def utility_processor():
    return dict(translate=get_translation)

@app.route('/snapshots', methods=['GET'])
def snapshot_manager():
    snapshots = load_snapshots()
    return render_template('snapshots.html', snapshots=snapshots)

@app.route('/snapshots/create', methods=['POST'])
def create_snapshot():
    snapshots = load_snapshots()
    new_id = 1 + max([s.get('id', 0) for s in snapshots], default=0)
    # Recherche globale : tout, tout, partout
    activities = search_activities('Tous', 'Tous')
    housings = search_housings('Tous', 'Tous')
    restaurants = search_restaurants('Tous', 'Tous')
    new_snapshot = {
        'id': new_id,
        'name': f'Snapshot {new_id}',
        'created_at': datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        'data': {
            'activities': activities,
            'housings': housings,
            'restaurants': restaurants
        },
    }
    snapshots.append(new_snapshot)
    save_snapshots(snapshots)
    return redirect(url_for('snapshot_manager'))

@app.route('/snapshots/delete/<int:snap_id>', methods=['GET'])
def delete_snapshot(snap_id):
    snapshots = load_snapshots()
    snapshots = [s for s in snapshots if s.get('id') != snap_id]
    save_snapshots(snapshots)
    return redirect(url_for('snapshot_manager'))

@app.route('/snapshots/view/<int:snap_id>', methods=['GET'])
def view_snapshot(snap_id):
    snapshots = load_snapshots()
    snap = next((s for s in snapshots if s.get('id') == snap_id), None)
    if not snap:
        return redirect(url_for('snapshot_manager'))
    return render_template('snapshots_detail.html', snapshot=snap)

@app.route('/snapshots/create_async')
def create_snapshot_async():
    # Démarre le thread de création si pas déjà en cours
    if not os.path.exists(PROGRESS_FILE):
        t = threading.Thread(target=run_snapshot_creation)
        t.start()
    return render_template('snapshots_creating.html')

@app.route('/snapshots/progress')
def snapshot_progress():
    if not os.path.exists(PROGRESS_FILE):
        return jsonify({"activities": 0, "housings": 0, "restaurants": 0, "status": "En attente…", "done": False})
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

def run_snapshot_creation():
    progress = {"activities": 0, "housings": 0, "restaurants": 0, "status": "Démarrage…", "done": False}
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    # 1. Activités
    progress["status"] = "Recherche des activités…"
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    activities = {}
    countries = list(PARKS_URLS.keys())
    all_parks = [(country, park) for country in countries for park in PARKS_URLS[country].keys()]
    total = len(all_parks)
    for i, (country, park) in enumerate(all_parks):
        activities.setdefault(country, {})[park] = activity_service.get_activities_with_placeholders(PARKS_URLS[country][park]["activities"])
        progress["activities"] = int((i+1)/total*100)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f)
    # 2. Hébergements
    progress["status"] = "Recherche des hébergements…"
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    housings = {}
    for i, (country, park) in enumerate(all_parks):
        housings.setdefault(country, {})[park] = housing_service.get_housings_with_placeholders(PARKS_URLS[country][park]["cottages"])
        progress["housings"] = int((i+1)/total*100)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f)
    # 3. Restaurants
    progress["status"] = "Recherche des restaurants…"
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    restaurants = {}
    for i, (country, park) in enumerate(all_parks):
        restaurants.setdefault(country, {})[park] = restaurant_service.get_restaurants_with_placeholders(PARKS_URLS[country][park]["restaurants"])
        progress["restaurants"] = int((i+1)/total*100)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f)
    # Finalisation
    progress["status"] = "Sauvegarde du snapshot…"
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    # Ajout du snapshot
    snapshots = load_snapshots()
    new_id = 1 + max([s.get('id', 0) for s in snapshots], default=0)
    new_snapshot = {
        'id': new_id,
        'name': f'Snapshot {new_id}',
        'created_at': datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        'data': {
            'activities': activities,
            'housings': housings,
            'restaurants': restaurants
        },
    }
    snapshots.append(new_snapshot)
    save_snapshots(snapshots)
    progress["status"] = "Terminé !"
    progress["done"] = True
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    # Nettoyage du fichier d'avancement après quelques secondes
    time.sleep(3)
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"=== FLASK EN ÉCOUTE SUR http://0.0.0.0:{port} ===")
    app.run(host="0.0.0.0", port=port, debug=True)
