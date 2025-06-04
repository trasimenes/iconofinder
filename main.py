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
from utils.stats import compute_stats

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


def search_activities(country, parc, logs=None):
    if logs is None:
        logs = []
    logs.append(f"[ACTIVITÉS] Début recherche pour {country} - {parc}")
    final_results = {}
    countries_to_process = [country] if country != "Tous" else PARKS_URLS.keys()
    for current_country in countries_to_process:
        if parc == "Tous":
            all_parks_results = {}
            for park_name, park_urls in PARKS_URLS.get(current_country, {}).items():
                activities_url = park_urls.get("activities")
                if activities_url:
                    logs.append(f"[ACTIVITÉS] {current_country} - {park_name}")
                    result = activity_service.get_activities_with_placeholders(activities_url)
                    result["url"] = activities_url
                    all_parks_results[park_name] = result
            if all_parks_results:
                final_results[current_country] = all_parks_results
        else:
            activities_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("activities")
            if activities_url:
                logs.append(f"[ACTIVITÉS] {current_country} - {parc}")
                result = activity_service.get_activities_with_placeholders(activities_url)
                result["url"] = activities_url
                final_results[current_country] = {parc: result}
    logs.append(f"[ACTIVITÉS] Fin recherche pour {country} - {parc}")
    return final_results

def search_housings(country, parc, logs=None):
    if logs is None:
        logs = []
    logs.append(f"[HÉBERGEMENTS] Début recherche pour {country} - {parc}")
    final_results = {}
    countries_to_process = [country] if country != "Tous" else PARKS_URLS.keys()
    for current_country in countries_to_process:
        if parc == "Tous":
            all_parks_results = {}
            for park_name, park_urls in PARKS_URLS.get(current_country, {}).items():
                cottages_url = park_urls.get("cottages")
                if cottages_url:
                    logs.append(f"[HÉBERGEMENTS] {current_country} - {park_name}")
                    result = housing_service.get_housings_with_placeholders(cottages_url)
                    result["url"] = cottages_url
                    all_parks_results[park_name] = result
            if all_parks_results:
                final_results[current_country] = all_parks_results
        else:
            cottages_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("cottages")
            if cottages_url:
                logs.append(f"[HÉBERGEMENTS] {current_country} - {parc}")
                result = housing_service.get_housings_with_placeholders(cottages_url)
                result["url"] = cottages_url
                final_results[current_country] = {parc: result}
    logs.append(f"[HÉBERGEMENTS] Fin recherche pour {country} - {parc}")
    return final_results

def search_restaurants(country, parc, logs=None):
    if logs is None:
        logs = []
    logs.append(f"[RESTAURANTS] Début recherche pour {country} - {parc}")
    final_results = {}
    countries_to_process = [country] if country != "Tous" else PARKS_URLS.keys()
    for current_country in countries_to_process:
        if parc == "Tous":
            all_parks_results = {}
            for park_name, park_urls in PARKS_URLS.get(current_country, {}).items():
                restaurants_url = park_urls.get("restaurants")
                if restaurants_url:
                    logs.append(f"[RESTAURANTS] {current_country} - {park_name}")
                    result = restaurant_service.get_restaurants_with_placeholders(restaurants_url)
                    result["url"] = restaurants_url
                    all_parks_results[park_name] = result
            if all_parks_results:
                final_results[current_country] = all_parks_results
        else:
            restaurants_url = PARKS_URLS.get(current_country, {}).get(parc, {}).get("restaurants")
            if restaurants_url:
                logs.append(f"[RESTAURANTS] {current_country} - {parc}")
                result = restaurant_service.get_restaurants_with_placeholders(restaurants_url)
                result["url"] = restaurants_url
                final_results[current_country] = {parc: result}
    logs.append(f"[RESTAURANTS] Fin recherche pour {country} - {parc}")
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
    logs = []
    country = request.args.get('country')
    parc = request.args.get('parc')
    search_type = request.args.get('type')
    if not all([country, parc, search_type]):
        return jsonify({'error': 'Paramètres manquants', 'logs': logs})
    try:
        if search_type == "Hébergements":
            results = search_housings(country, parc, logs=logs)
        elif search_type == "Activités":
            results = search_activities(country, parc, logs=logs)
        elif search_type == "Restaurants":
            results = search_restaurants(country, parc, logs=logs)
        else:
            return jsonify({'error': 'Type de recherche non valide', 'logs': logs})
        return jsonify(results=results, logs=logs)
    except Exception as e:
        logs.append(f"[ERREUR] {str(e)}")
        return jsonify({'error': str(e), 'logs': logs})

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

@app.route('/stats')
def stats_view():
    snapshots = load_snapshots()
    if not snapshots:
        return render_template('stats.html', stats=None, translate=get_translation)
    data = snapshots[-1]['data']
    stats_data = compute_stats(data)
    return render_template('stats.html', stats=stats_data, translate=get_translation)

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
    return redirect(url_for('snapshot_manager', status='success'))

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
    try:
        if not os.path.exists(PROGRESS_FILE):
            return jsonify({"activities": 0, "housings": 0, "restaurants": 0, "status": "En attente…", "done": False, "logs": []})
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                # Fichier vide, on retourne un état d'attente
                return jsonify({"activities": 0, "housings": 0, "restaurants": 0, "status": "En attente…", "done": False, "logs": []})
            return jsonify(json.loads(content))
    except Exception as e:
        return jsonify({"activities": 0, "housings": 0, "restaurants": 0, "status": f"Erreur: {str(e)}", "done": False, "logs": []}), 200

def run_snapshot_creation():
    progress = {"activities": 0, "housings": 0, "restaurants": 0, "status": "Démarrage…", "done": False, "logs": []}
    def log(msg):
        print(msg)
        progress["logs"].append(msg)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f)
    log("Début de la création du snapshot")
    # 1. Activités
    progress["status"] = "Recherche des activités…"
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)
    activities = {}
    countries = list(PARKS_URLS.keys())
    all_parks = [(country, park) for country in countries for park in PARKS_URLS[country].keys()]
    total = len(all_parks)
    for i, (country, park) in enumerate(all_parks):
        log(f"[ACTIVITÉS] {country} - {park}")
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
        log(f"[HÉBERGEMENTS] {country} - {park}")
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
        log(f"[RESTAURANTS] {country} - {park}")
        restaurants.setdefault(country, {})[park] = restaurant_service.get_restaurants_with_placeholders(PARKS_URLS[country][park]["restaurants"])
        progress["restaurants"] = int((i+1)/total*100)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f)
    # Finalisation
    log("Fin de la création du snapshot")
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
    time.sleep(3)
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"=== FLASK EN ÉCOUTE SUR http://0.0.0.0:{port} ===")
    app.run(host="0.0.0.0", port=port, debug=True)
