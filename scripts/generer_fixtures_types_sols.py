"""Genere referentiel/fixtures/types_sols.json avec les 7 VRAIS types de sols du
dataset Kaggle "Comprehensive Soil Classification Datasets" (AI4A Lab), utilises par
le classificateur d'image, et met a jour les associations sols_favorables des
cultures (referentiel/fixtures/cultures.json) selon des correspondances agronomiques
generales reconnues (FAO ; Baize, Guide des analyses en pedologie).
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = BASE_DIR / 'referentiel' / 'fixtures'

# code (identique au libelle du dataset d'images) -> (libelle FR, description, ph_min, ph_max, couleur)
TYPES_SOLS = {
    'Alluvial_Soil': (
        'Sol alluvial', "Sol fertile depose par les cours d'eau, riche en limon, texture equilibree.",
        6.0, 7.5, '#8d6e63',
    ),
    'Arid_Soil': (
        'Sol aride', "Sol pauvre en matiere organique, faible retention d'eau, typique des zones seches.",
        7.5, 9.0, '#d7ccc8',
    ),
    'Black_Soil': (
        'Sol noir (regur)', 'Sol argileux riche en fer et magnesium, forte retention hydrique.',
        6.5, 8.0, '#3e2723',
    ),
    'Laterite_Soil': (
        'Sol lateritique', "Sol tropical lessive, riche en oxydes de fer et d'aluminium, pauvre en nutriments.",
        5.0, 6.5, '#bf360c',
    ),
    'Mountain_Soil': (
        'Sol de montagne', "Sol peu profond et caillouteux, forme sur pente, riche en matiere organique en surface.",
        5.5, 7.0, '#6d4c41',
    ),
    'Red_Soil': (
        'Sol rouge', 'Sol riche en oxyde de fer, texture legère, drainage rapide, pauvre en azote.',
        5.5, 7.0, '#c62828',
    ),
    'Yellow_Soil': (
        'Sol jaune', 'Variante hydratee du sol rouge, drainage limite, acidite marquee.',
        5.0, 6.5, '#f9a825',
    ),
}

# Correspondances agronomiques generales (sols favorables par culture), non exhaustives :
# etablies a partir des exigences texturales et de drainage usuelles de chaque culture.
CULTURES_VERS_SOLS = {
    'Riz': ['Alluvial_Soil', 'Black_Soil'],
    'Mais': ['Alluvial_Soil', 'Black_Soil', 'Red_Soil'],
    'Pois chiche': ['Black_Soil', 'Alluvial_Soil'],
    'Haricot rouge': ['Alluvial_Soil', 'Mountain_Soil'],
    "Pois d'Angole": ['Red_Soil', 'Black_Soil'],
    'Haricot moth': ['Arid_Soil', 'Red_Soil'],
    'Haricot mungo': ['Alluvial_Soil', 'Red_Soil'],
    'Haricot noir': ['Black_Soil', 'Alluvial_Soil'],
    'Lentille': ['Alluvial_Soil', 'Black_Soil'],
    'Grenade': ['Arid_Soil', 'Red_Soil'],
    'Banane': ['Alluvial_Soil', 'Laterite_Soil'],
    'Mangue': ['Laterite_Soil', 'Red_Soil', 'Alluvial_Soil'],
    'Raisin': ['Black_Soil', 'Red_Soil'],
    'Pasteque': ['Alluvial_Soil', 'Red_Soil'],
    'Melon': ['Alluvial_Soil', 'Arid_Soil'],
    'Pomme': ['Mountain_Soil'],
    'Orange': ['Red_Soil', 'Alluvial_Soil'],
    'Papaye': ['Laterite_Soil', 'Alluvial_Soil'],
    'Noix de coco': ['Laterite_Soil', 'Alluvial_Soil'],
    'Coton': ['Black_Soil', 'Alluvial_Soil'],
    'Jute': ['Alluvial_Soil'],
    'Cafe': ['Laterite_Soil', 'Mountain_Soil'],
}

types_sols = []
code_vers_pk = {}
for i, (code, (libelle, description, ph_min, ph_max, couleur)) in enumerate(TYPES_SOLS.items(), start=1):
    code_vers_pk[code] = i
    types_sols.append({
        'model': 'referentiel.typesol',
        'pk': i,
        'fields': {
            'code': code, 'libelle': libelle, 'description': description,
            'ph_min': ph_min, 'ph_max': ph_max, 'couleur_hex': couleur,
        },
    })
(FIXTURES_DIR / 'types_sols.json').write_text(json.dumps(types_sols, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(types_sols)} types de sols (reels) ecrits.')

# Mise a jour des sols_favorables dans cultures.json (le fichier doit deja exister,
# genere par generer_fixtures_referentiel.py)
chemin_cultures = FIXTURES_DIR / 'cultures.json'
cultures = json.loads(chemin_cultures.read_text(encoding='utf-8'))
for culture in cultures:
    nom = culture['fields']['nom']
    codes_sols = CULTURES_VERS_SOLS.get(nom, [])
    culture['fields']['sols_favorables'] = [code_vers_pk[c] for c in codes_sols]
chemin_cultures.write_text(json.dumps(cultures, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(cultures)} cultures mises a jour avec leurs sols favorables reels.')
