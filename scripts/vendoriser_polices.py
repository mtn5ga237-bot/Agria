"""Telecharge les fichiers de polices Google Fonts (Inter, Space Grotesk) localement,
en ne conservant que les sous-ensembles latin/latin-ext, et reecrit le CSS avec des
chemins locaux. Permet un fonctionnement hors-ligne complet (cf. contrainte de
connectivite intermittente du rapport de stage).
"""
import re
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'static' / 'vendor' / 'fonts'
CSS_SRC = BASE / 'inter.css'
CSS_OUT = BASE / 'polices.css'
(BASE / 'files').mkdir(parents=True, exist_ok=True)

texte = CSS_SRC.read_text(encoding='utf-8')

blocs = re.findall(r'/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})', texte)
sortie = []
compte = 0
for sous_ensemble, bloc in blocs:
    if sous_ensemble not in ('latin', 'latin-ext'):
        continue
    url_match = re.search(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', bloc)
    if not url_match:
        continue
    url = url_match.group(1)
    nom_fichier = url.split('/')[-1]
    chemin_local = BASE / 'files' / nom_fichier
    if not chemin_local.exists():
        urllib.request.urlretrieve(url, chemin_local)
        compte += 1
    bloc_local = bloc.replace(url, f'files/{nom_fichier}')
    sortie.append(bloc_local)

CSS_OUT.write_text('\n'.join(sortie), encoding='utf-8')
print(f'{compte} fichiers telecharges, {len(sortie)} regles @font-face ecrites dans {CSS_OUT}')
