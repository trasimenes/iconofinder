import json
from flask import session

def load_translations():
    """Load translations from the JSON file."""
    with open("translations/translations.json", "r", encoding="utf-8") as file:
        return json.load(file)

translations = load_translations()

def get_translation(key):
    """Get translation for a given key in the current language."""
    lang = session.get("lang", "fr")
    return translations.get(lang, {}).get(key, key) 