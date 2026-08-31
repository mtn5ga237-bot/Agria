"""Pipeline d'entrainement du classificateur de type de sol par photographie.

Entraine sur le jeu de donnees Kaggle "Comprehensive Soil Classification Datasets"
(AI4A Lab), variante CyAUG (augmentee par CycleGAN, 7 classes, ~5100 images), pour
disposer d'un corpus suffisamment large et equilibre. Suit le meme schema
d'evaluation que le modele de recommandation de cultures (Dossier VI du rapport) :
partition stratifiee 80/20, Random Forest, metriques completes.
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from .image_features import extraire_caracteristiques

EXTENSIONS_VALIDES = {'.jpg', '.jpeg', '.png', '.webp'}


def lister_images(repertoire_dataset):
    """Parcourt un repertoire organise en sous-dossiers <NomClasse>/*.jpg et retourne
    la liste (chemin, libelle)."""
    repertoire_dataset = Path(repertoire_dataset)
    elements = []
    for dossier_classe in sorted(repertoire_dataset.iterdir()):
        if not dossier_classe.is_dir():
            continue
        for fichier in dossier_classe.iterdir():
            if fichier.suffix.lower() in EXTENSIONS_VALIDES:
                elements.append((fichier, dossier_classe.name))
    return elements


def preparer_donnees(repertoire_dataset):
    elements = lister_images(repertoire_dataset)
    X, y = [], []
    for chemin, libelle in elements:
        try:
            X.append(extraire_caracteristiques(chemin))
            y.append(libelle)
        except Exception:
            continue
    return np.array(X), np.array(y)


def entrainer(repertoire_dataset, chemin_sortie):
    X, y = preparer_donnees(repertoire_dataset)

    encodeur = LabelEncoder()
    y_encode = encodeur.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encode, test_size=0.2, random_state=42, stratify=y_encode,
    )

    modele = RandomForestClassifier(
        n_estimators=300, max_depth=20, min_samples_split=4, min_samples_leaf=2,
        class_weight='balanced', random_state=42, n_jobs=-1,
    )
    modele.fit(X_train, y_train)

    y_pred = modele.predict(X_test)
    metriques = {
        'exactitude': float(accuracy_score(y_test, y_pred)),
        'f1': float(f1_score(y_test, y_pred, average='weighted')),
        'matrice_confusion': confusion_matrix(y_test, y_pred).tolist(),
        'rapport': classification_report(y_test, y_pred, target_names=encodeur.classes_, zero_division=0),
        'nb_observations': len(y),
        'nb_test': len(y_test),
    }

    chemin_sortie = Path(chemin_sortie)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'modele': modele, 'encodeur': encodeur, 'classes': list(encodeur.classes_)}, chemin_sortie)

    return metriques
