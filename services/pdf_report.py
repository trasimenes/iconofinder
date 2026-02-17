import os
import re
import json
import datetime
import subprocess
import tempfile
import requests
from jinja2 import Template

DEFAULT_FRAGMENT = 'default/'
DISPLAY_RATE_EXPONENT = 0.5

# French → English country name mapping
COUNTRY_NAMES_EN = {
    'France': 'France',
    'Belgique': 'Belgium',
    'Allemagne': 'Germany',
    'Pays-Bas': 'Netherlands',
    'Danemark': 'Denmark',
}

# Park cover image IDs (scraped from park overview pages)
PARK_COVER_IDS = {
    "Villages Nature Paris": "AAA_145657",
    "Le Lac d'Ailette": "AAA_165385",
    "Les Hauts de Bruyères": "AAA_154348",
    "Le Bois aux Daims": "AAA_160878",
    "Les Bois-Francs": "AAA_160136",
    "Les Trois Forêts": "AAA_161834",
    "Les Landes de Gascogne": "AAA_167962",
    "Les Ardennes": "AAA_164825",
    "De Vossemeren": "AAA_155017",
    "Erperheide": "AAA_165342",
    "Park De Haan": "AAA_59804",
    "Terhills Resort": "AAA_155823",
    "Park Bostalsee": "AAA_153589",
    "Park Hochsauerland": "AAA_167634",
    "Park Allgäu": "AAA_153573",
    "Bispinger Heide": "AAA_153578",
    "Park Nordseeküste": "AAA_161770",
    "Park Eifel": "AAA_161266",
    "Port Zélande": "AAA_165981",
    "Het Heijderbos": "AAA_156728",
    "Park Zandvoort": "AAA_154664",
    "De Kempervennen": "AAA_154612",
    "De Huttenheugte": "AAA_174788",
    "De Eemhof": "AAA_154873",
    "Het Meerdal": "AAA_153504",
    "Parc Sandur": "AAA_169922",
    "Limburgse Peel": "AAA_171616",
    "Nordborg Resort": "AAA_172249",
}

COVER_BASE_URL = "https://photos.centerparcs.com/admin/fp2/photos/169/566x250"
COVERS_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'park_covers')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'report_template.html')

# Chrome paths to try
CHROME_PATHS = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
]


def _find_chrome():
    """Find Chrome executable."""
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    return None


def _html_to_pdf(html_content, output_path):
    """Convert HTML to PDF using Chrome headless."""
    chrome = _find_chrome()
    if not chrome:
        raise RuntimeError("Chrome not found. Install Google Chrome to generate PDF reports.")

    with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
        f.write(html_content)
        html_path = f.name

    try:
        cmd = [
            chrome,
            '--headless=new',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-software-rasterizer',
            f'--print-to-pdf={output_path}',
            '--print-to-pdf-no-header',
            f'file://{html_path}'
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
    finally:
        os.unlink(html_path)


# ─── Cover image management ───

def _get_cover_url(park_name):
    img_id = PARK_COVER_IDS.get(park_name)
    if not img_id:
        return None
    return f'{COVER_BASE_URL}/{img_id}_169.jpg'


def _download_cover(park_name, cache_dir=None):
    if cache_dir is None:
        cache_dir = COVERS_CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)

    safe_name = re.sub(r'[^\w\-]', '_', park_name)
    local_path = os.path.join(cache_dir, f'{safe_name}.jpg')

    if os.path.exists(local_path):
        return local_path

    url = _get_cover_url(park_name)
    if not url:
        return None

    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'curl/8.7.1'})
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return local_path
    except Exception:
        pass
    return None


def _ensure_covers(park_names, cache_dir=None):
    if cache_dir is None:
        cache_dir = COVERS_CACHE_DIR
    covers = {}
    for name in park_names:
        path = _download_cover(name, cache_dir)
        if path:
            covers[name] = path
    return covers


# ─── Missing items detection ───

def _is_missing_activity(item):
    if 'has_photos' in item:
        return not item.get('has_photos')
    image_src = item.get('image_src', '')
    return not image_src or DEFAULT_FRAGMENT in image_src


def _is_missing_housing(item):
    if 'has_photos' in item:
        return not item.get('has_photos')
    image_src = item.get('image_src', '')
    return not image_src or DEFAULT_FRAGMENT in image_src


def _is_missing_restaurant(item):
    if 'has_photos' in item:
        return not item.get('has_photos')
    image_src = item.get('image_src', '')
    return (not image_src or DEFAULT_FRAGMENT in image_src or
            len(item.get('images', [])) == 0)


def _is_missing_surrounding(item):
    if 'has_photos' in item:
        return not item.get('has_photos')
    image_src = item.get('image_src', '')
    return not image_src or DEFAULT_FRAGMENT in image_src


EMPTY_PARK = {'activities': [], 'housings': [], 'restaurants': [], 'surroundings': []}


def _extract_missing_items(snapshot_data, country, include=None):
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}
    parks = {}

    if 'activities' in include:
        for park_name, park_data in snapshot_data.get('activities', {}).get(country, {}).items():
            if park_name not in parks:
                parks[park_name] = {k: [] for k in EMPTY_PARK}
            for item in park_data.get('activities', []):
                if _is_missing_activity(item):
                    parks[park_name]['activities'].append({
                        'name': item.get('name', 'Unknown')
                    })

    if 'housings' in include:
        for park_name, park_data in snapshot_data.get('housings', {}).get(country, {}).items():
            if park_name not in parks:
                parks[park_name] = {k: [] for k in EMPTY_PARK}
            for item in park_data.get('housings', []):
                if _is_missing_housing(item):
                    parks[park_name]['housings'].append({
                        'name': item.get('name', 'Unknown'),
                        'type': item.get('type', '?')
                    })

    if 'restaurants' in include:
        for park_name, park_data in snapshot_data.get('restaurants', {}).get(country, {}).items():
            if park_name not in parks:
                parks[park_name] = {k: [] for k in EMPTY_PARK}
            for item in park_data.get('restaurants', []):
                if _is_missing_restaurant(item):
                    parks[park_name]['restaurants'].append({
                        'name': item.get('name', 'Unknown')
                    })

    if 'surroundings' in include:
        for park_name, park_data in snapshot_data.get('surroundings', {}).get(country, {}).items():
            if park_name not in parks:
                parks[park_name] = {k: [] for k in EMPTY_PARK}
            for item in park_data.get('surroundings', []):
                if _is_missing_surrounding(item):
                    parks[park_name]['surroundings'].append({
                        'name': item.get('name', 'Unknown')
                    })

    return parks


def _compute_totals(parks):
    totals = {'activities': 0, 'housings': 0, 'restaurants': 0, 'surroundings': 0}
    for park_data in parks.values():
        totals['activities'] += len(park_data['activities'])
        totals['housings'] += len(park_data['housings'])
        totals['restaurants'] += len(park_data['restaurants'])
        totals['surroundings'] += len(park_data.get('surroundings', []))
    return totals


def _compute_item_totals(snapshot_data, country, include=None):
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}
    totals = {'activities': 0, 'housings': 0, 'restaurants': 0, 'surroundings': 0}

    if 'activities' in include:
        for park_data in snapshot_data.get('activities', {}).get(country, {}).values():
            totals['activities'] += len(park_data.get('activities', []))

    if 'housings' in include:
        for park_data in snapshot_data.get('housings', {}).get(country, {}).values():
            totals['housings'] += len(park_data.get('housings', []))

    if 'restaurants' in include:
        for park_data in snapshot_data.get('restaurants', {}).get(country, {}).values():
            totals['restaurants'] += len(park_data.get('restaurants', []))

    if 'surroundings' in include:
        for park_data in snapshot_data.get('surroundings', {}).get(country, {}).values():
            totals['surroundings'] += len(park_data.get('surroundings', []))

    return totals


def _scale_missing_rate(rate, exponent=DISPLAY_RATE_EXPONENT):
    normalized = max(0.0, min(1.0, rate / 100))
    return (normalized ** exponent) * 100


# ─── Build template data ───

def _build_report_data(snapshot_data, country_filter=None, include=None, for_browser=False):
    """Build the full data structure for the HTML template."""
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}

    all_country_names = sorted(set(
        list(snapshot_data.get('activities', {}).keys()) +
        list(snapshot_data.get('housings', {}).keys()) +
        list(snapshot_data.get('restaurants', {}).keys()) +
        list(snapshot_data.get('surroundings', {}).keys())
    ))

    if country_filter and country_filter != 'all':
        all_country_names = [c for c in all_country_names if c == country_filter]

    # Collect all park names for cover images
    all_park_names = []
    countries = []

    for country_name in all_country_names:
        parks_data = _extract_missing_items(snapshot_data, country_name, include)
        totals = _compute_totals(parks_data)
        item_totals = _compute_item_totals(snapshot_data, country_name, include)
        missing_rates = {}
        missing_rates_display = {}
        for key in totals:
            total_items = item_totals.get(key, 0)
            if total_items > 0:
                missing_rates[key] = min(100, (totals[key] / total_items) * 100)
            else:
                missing_rates[key] = 0
            missing_rates_display[key] = _scale_missing_rate(missing_rates[key])

        parks_list = []
        for park_name in sorted(parks_data.keys()):
            all_park_names.append(park_name)
            parks_list.append({
                'name': park_name,
                'missing': parks_data[park_name],
                'cover': None,  # filled after download
            })

        display_name = COUNTRY_NAMES_EN.get(country_name, country_name)
        countries.append({
            'name': display_name,
            'parks': parks_list,
            'totals': totals,
            'item_totals': item_totals,
            'missing_rates': missing_rates,
            'missing_rates_display': missing_rates_display,
        })

    # Set cover image URLs
    if for_browser:
        for c in countries:
            for park in c['parks']:
                url = _get_cover_url(park['name'])
                if url:
                    park['cover'] = url
    else:
        covers = _ensure_covers(all_park_names)
        for c in countries:
            for park in c['parks']:
                cover_path = covers.get(park['name'])
                if cover_path:
                    park['cover'] = f'file://{os.path.abspath(cover_path)}'

    # Grand totals
    grand_totals = {'activities': 0, 'housings': 0, 'restaurants': 0, 'surroundings': 0}
    for c in countries:
        for k in grand_totals:
            grand_totals[k] += c['totals'][k]

    # Max total for bar chart scaling
    max_total = max(
        (c['totals']['activities'] + c['totals']['housings'] + c['totals']['restaurants'] + c['totals']['surroundings']
         for c in countries),
        default=1
    ) or 1

    total_parks = sum(len(c['parks']) for c in countries)

    return {
        'countries': countries,
        'grand_totals': grand_totals,
        'max_total': max_total,
        'total_parks': total_parks,
    }


def _render_html(data, report_title, date_str, for_browser=False):
    """Render the HTML template with data."""
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = Template(f.read())

    if for_browser:
        fonts_dir = '/static/fonts'
    else:
        fonts_dir = f'file://{os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))}'

    return template.render(
        fonts_dir=fonts_dir,
        report_title=report_title,
        date_str=date_str,
        for_browser=for_browser,
        **data,
    )


# ─── Public API ───

def render_country_report_html(country, snapshot_data, include=None):
    """Render report HTML for browser display. Returns HTML string."""
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}
    date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    data = _build_report_data(snapshot_data, country_filter=country, include=include, for_browser=True)
    title = COUNTRY_NAMES_EN.get(country, country)
    return _render_html(data, title, date_str, for_browser=True)


def render_global_report_html(snapshot_data, include=None):
    """Render report HTML for browser display. Returns HTML string."""
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}
    date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    data = _build_report_data(snapshot_data, country_filter=None, include=include, for_browser=True)
    return _render_html(data, 'All countries', date_str, for_browser=True)


def generate_country_report(country, snapshot_data, output_dir, include=None):
    """Generate a PDF report for a single country. Returns the file path."""
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}

    date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    data = _build_report_data(snapshot_data, country_filter=country, include=include)
    title = COUNTRY_NAMES_EN.get(country, country)
    html = _render_html(data, title, date_str)

    os.makedirs(output_dir, exist_ok=True)
    safe_name = country.replace(' ', '_').replace("'", '')
    filename = f'report_{safe_name}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    filepath = os.path.join(output_dir, filename)

    _html_to_pdf(html, filepath)
    return filepath


def generate_global_report(snapshot_data, output_dir, include=None):
    """Generate a PDF report for all countries. Returns the file path."""
    if include is None:
        include = {'activities', 'housings', 'restaurants', 'surroundings'}

    date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    data = _build_report_data(snapshot_data, country_filter=None, include=include)
    html = _render_html(data, 'All countries', date_str)

    os.makedirs(output_dir, exist_ok=True)
    filename = f'report_global_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    filepath = os.path.join(output_dir, filename)

    _html_to_pdf(html, filepath)
    return filepath


def list_reports(output_dir):
    """List all generated PDF reports with metadata."""
    if not os.path.exists(output_dir):
        return []
    reports = []
    for filename in sorted(os.listdir(output_dir), reverse=True):
        if filename.endswith('.pdf'):
            filepath = os.path.join(output_dir, filename)
            stat = os.stat(filepath)
            size_kb = round(stat.st_size / 1024, 1)
            created = datetime.datetime.fromtimestamp(stat.st_mtime)
            reports.append({
                'filename': filename,
                'created_at': created.strftime('%d/%m/%Y %H:%M:%S'),
                'size': f'{size_kb} KB'
            })
    return reports
