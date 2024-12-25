import os
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import traceback


app = Flask(__name__)

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




# Créer l'application Flask
app = Flask(__name__)

# Définir les URLs du placeholder
placeholder_base_url = "https://static.centerparcs.com"
placeholder_image_suffix = "/common/assets/images/default/500x375.jpg"


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/recherche')
def recherche():
    return render_template('search.html', parcs=parcs)


from concurrent.futures import ThreadPoolExecutor

@app.route('/results', methods=['GET'])
def results():
    # Récupérer les données du formulaire
    country = request.args.get('country')
    parc = request.args.get('parc')

    if not country or not parc:
        return "Pays ou parc non spécifié."

    final_results = {}

    # Cas où tous les pays sont sélectionnés
    if country == "Tous" and parc == "Tous":
        for country_name, parks in parcs.items():
            final_results[country_name] = {}
            for parc_name, parc_url in parks.items():
                activities = get_activities_with_placeholders(parc_url)
                final_results[country_name][parc_name] = activities

    # Cas où un pays spécifique est sélectionné avec tous les parcs
    elif parc == "Tous":
        if country in parcs:
            final_results[country] = {}
            for parc_name, parc_url in parcs[country].items():
                activities = get_activities_with_placeholders(parc_url)
                final_results[country][parc_name] = activities

    # Cas où un pays et un parc spécifique sont sélectionnés
    else:
        parc_url = parcs.get(country, {}).get(parc)
        if not parc_url:
            return "Parc ou URL invalide."

        activities = get_activities_with_placeholders(parc_url)
        final_results[country] = {parc: activities}

    # Vérification des résultats
    print(f"DEBUG: Final Results = {final_results}")

    # Renvoyer les résultats au template
    return render_template('results.html', results=final_results)


# Fonction pour extraire les activités avec placeholders
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
        return activities_with_placeholder if activities_with_placeholder else ["Aucune activité trouvée."]
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        return ["Erreur lors du scraping."]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)