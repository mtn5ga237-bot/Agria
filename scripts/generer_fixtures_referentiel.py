"""Genere les fixtures referentiel/fixtures/types_sols.json et cultures.json a partir
des statistiques reelles du jeu de donnees Kaggle (Crop_recommendation.csv) et de
connaissances agronomiques generales, conformement au Dossier IV (classes TypeSol et
Culture) et au Tableau 16 (bareme de recommandation).

Usage : env/Scripts/python.exe scripts/generer_fixtures_referentiel.py
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CSV = BASE_DIR / 'donnees' / 'Crop_recommendation.csv'
FIXTURES_DIR = BASE_DIR / 'referentiel' / 'fixtures'
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# Traduction francaise, cycle vegetatif indicatif (jours) et couleur d'affichage
# pour chacune des 22 cultures du corpus (connaissances agronomiques generales).
META = {
    'rice':        {'nom': 'Riz',              'sci': 'Oryza sativa',            'cycle': 120, 'couleur': '#2e7d32'},
    'maize':       {'nom': 'Mais',              'sci': 'Zea mays',                'cycle': 100, 'couleur': '#fdd835'},
    'chickpea':    {'nom': 'Pois chiche',        'sci': 'Cicer arietinum',         'cycle': 100, 'couleur': '#8d6e63'},
    'kidneybeans': {'nom': 'Haricot rouge',      'sci': 'Phaseolus vulgaris',      'cycle': 90,  'couleur': '#c62828'},
    'pigeonpeas':  {'nom': "Pois d'Angole",      'sci': 'Cajanus cajan',           'cycle': 150, 'couleur': '#6d4c41'},
    'mothbeans':   {'nom': 'Haricot moth',       'sci': 'Vigna aconitifolia',      'cycle': 75,  'couleur': '#a1887f'},
    'mungbean':    {'nom': 'Haricot mungo',      'sci': 'Vigna radiata',           'cycle': 65,  'couleur': '#9ccc65'},
    'blackgram':   {'nom': 'Haricot noir',       'sci': 'Vigna mungo',             'cycle': 90,  'couleur': '#424242'},
    'lentil':      {'nom': 'Lentille',           'sci': 'Lens culinaris',          'cycle': 110, 'couleur': '#8e7cc3'},
    'pomegranate': {'nom': 'Grenade',            'sci': 'Punica granatum',         'cycle': 180, 'couleur': '#ad1457'},
    'banana':      {'nom': 'Banane',             'sci': 'Musa spp.',               'cycle': 300, 'couleur': '#fbc02d'},
    'mango':       {'nom': 'Mangue',             'sci': 'Mangifera indica',        'cycle': 150, 'couleur': '#ef6c00'},
    'grapes':      {'nom': 'Raisin',             'sci': 'Vitis vinifera',          'cycle': 150, 'couleur': '#6a1b9a'},
    'watermelon':  {'nom': 'Pasteque',           'sci': 'Citrullus lanatus',       'cycle': 85,  'couleur': '#43a047'},
    'muskmelon':   {'nom': 'Melon',              'sci': 'Cucumis melo',            'cycle': 80,  'couleur': '#ffb300'},
    'apple':       {'nom': 'Pomme',              'sci': 'Malus domestica',         'cycle': 150, 'couleur': '#d32f2f'},
    'orange':      {'nom': 'Orange',             'sci': 'Citrus sinensis',         'cycle': 240, 'couleur': '#fb8c00'},
    'papaya':      {'nom': 'Papaye',             'sci': 'Carica papaya',           'cycle': 270, 'couleur': '#7cb342'},
    'coconut':     {'nom': 'Noix de coco',       'sci': 'Cocos nucifera',          'cycle': 365, 'couleur': '#795548'},
    'cotton':      {'nom': 'Coton',              'sci': 'Gossypium hirsutum',      'cycle': 180, 'couleur': '#1565c0'},
    'jute':        {'nom': 'Jute',               'sci': 'Corchorus olitorius',     'cycle': 120, 'couleur': '#558b2f'},
    'coffee':      {'nom': 'Cafe',               'sci': 'Coffea arabica',          'cycle': 270, 'couleur': '#4e342e'},
}

df = pd.read_csv(CSV)
stats = df.groupby('label').agg(
    ph_min=('ph', 'min'), ph_max=('ph', 'max'),
    n_med=('N', 'median'), p_med=('P', 'median'), k_med=('K', 'median'),
)

cultures = []
for i, label in enumerate(sorted(META), start=1):
    m = META[label]
    s = stats.loc[label]
    cultures.append({
        'model': 'referentiel.culture',
        'pk': i,
        'fields': {
            'code': label,
            'nom': m['nom'],
            'nom_scientifique': m['sci'],
            'ph_min': round(float(s.ph_min), 2),
            'ph_max': round(float(s.ph_max), 2),
            'cycle_jours': m['cycle'],
            'besoin_azote': round(float(s.n_med), 1),
            'besoin_phosphore': round(float(s.p_med), 1),
            'besoin_potassium': round(float(s.k_med), 1),
            'couleur_hex': m['couleur'],
            'description': f"Culture recommandee par le modele de classification pour un sol aux parametres proches de ceux du {m['nom'].lower()}.",
            'sols_favorables': [],
        },
    })

(FIXTURES_DIR / 'cultures.json').write_text(json.dumps(cultures, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(cultures)} cultures ecrites dans {FIXTURES_DIR}')
print("Executez ensuite generer_fixtures_types_sols.py pour les vrais types de sols et les associations.")
