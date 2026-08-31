"""Extraction de caracteristiques d'image pour la classification du type de sol.

Approche volontairement classique (histogrammes de couleur, statistiques de texture)
plutot qu'un reseau de neurones convolutif : elle reste dans l'esprit du reste du
projet (scikit-learn, Random Forest, faible cout de calcul) et respecte la contrainte
de puissance de calcul limitee identifiee dans le rapport de stage, tout en restant
suffisamment discriminante pour une classification par couleur et texture du sol.
"""

import numpy as np
from PIL import Image

TAILLE = (64, 64)
NB_CARACTERISTIQUES = 39


def _histogramme(canal, bins=8):
    hist, _ = np.histogram(canal, bins=bins, range=(0, 256))
    return hist / (hist.sum() + 1e-9)


def extraire_caracteristiques(chemin_ou_fichier):
    image = Image.open(chemin_ou_fichier).convert('RGB').resize(TAILLE)
    rgb = np.asarray(image, dtype=np.float32)
    hsv = np.asarray(image.convert('HSV'), dtype=np.float32)
    gris = np.asarray(image.convert('L'), dtype=np.float32)

    caracteristiques = []
    for i in range(3):
        canal = rgb[:, :, i]
        caracteristiques += [canal.mean(), canal.std()]
        caracteristiques += list(_histogramme(canal))
    for i in range(3):
        canal = hsv[:, :, i]
        caracteristiques += [canal.mean(), canal.std()]

    # Texture grossiere : variance globale et intensite moyenne des gradients (contraste local)
    gradient_x = np.abs(np.diff(gris, axis=1)).mean()
    gradient_y = np.abs(np.diff(gris, axis=0)).mean()
    caracteristiques += [gris.std(), gradient_x, gradient_y]

    return np.array(caracteristiques, dtype=np.float32)
