"""Pipeline d'entrainement du modele de classification d'AgriA (Dossier V, 6.1-6.2 ; Annexe 7).

Reproduit fidelement le pipeline decrit dans le rapport de stage : chargement du jeu de
donnees Kaggle « Crop Recommendation Dataset », ingenierie de deux variables derivees,
partition stratifiee 80/20, foret aleatoire dont les hyperparametres ont ete optimises
par recherche sur grille (grille reproduite ci-dessous a titre documentaire), evaluation
et serialisation au format joblib.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

VARIABLES_BASE = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
VARIABLES_DERIVEES = ['ratio_NK', 'indice_fertilite']
VARIABLES = VARIABLES_BASE + VARIABLES_DERIVEES

# Hyperparametres retenus a l'issue de la validation croisee a cinq blocs (Annexe 7c).
HYPERPARAMETRES = dict(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    criterion='gini',
    class_weight='balanced',
    random_state=42,
)

# Grille explored par GridSearchCV lors du reglage initial des hyperparametres (documentaire).
GRILLE_RECHERCHE = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 15, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
}


def ingenierie_variables(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['ratio_NK'] = df['N'] / df['K'].clip(lower=1)
    df['indice_fertilite'] = (df['N'] + df['P'] + df['K']) / 3
    return df


def preparer_donnees(chemin_csv) -> pd.DataFrame:
    df = pd.read_csv(chemin_csv)
    df = df.drop_duplicates()
    df = df[(df['ph'] >= 0) & (df['ph'] <= 14)]
    return ingenierie_variables(df)


def entrainer(chemin_csv, chemin_sortie, observations_supplementaires: pd.DataFrame | None = None):
    """Entraine un modele Random Forest et le serialise. Retourne le dict de metriques.

    Le parametre observations_supplementaires permet de fusionner des analyses validees
    par les experts pedologues au corpus d'origine, conformement au scenario de
    reentrainement decrit au Dossier III (2.3.c).
    """
    df = preparer_donnees(chemin_csv)
    if observations_supplementaires is not None and not observations_supplementaires.empty:
        df = pd.concat([df, ingenierie_variables(observations_supplementaires)], ignore_index=True)

    X = df[VARIABLES]
    encodeur = LabelEncoder()
    y = encodeur.fit_transform(df['label'])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    modele = RandomForestClassifier(**HYPERPARAMETRES)
    modele.fit(X_train, y_train)

    y_pred = modele.predict(X_test)
    metriques = {
        'exactitude': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        'rappel': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        'matrice_confusion': confusion_matrix(y_test, y_pred).tolist(),
        'rapport': classification_report(y_test, y_pred, target_names=encodeur.classes_, zero_division=0),
        'nb_observations': len(df),
        'nb_test': len(y_test),
        'importances': dict(zip(VARIABLES, modele.feature_importances_.tolist())),
    }

    chemin_sortie = Path(chemin_sortie)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        'modele': modele,
        'encodeur': encodeur,
        'classes': list(encodeur.classes_),
        'variables': VARIABLES,
        'metriques': metriques,
        'hyperparametres': HYPERPARAMETRES,
    }, chemin_sortie)

    return metriques
