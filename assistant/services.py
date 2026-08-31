"""Service de l'assistant AgriA.

Moteur de recherche par similarite (TF-IDF + similarite cosinus, scikit-learn) sur une
base de connaissances locale couvrant le fonctionnement de la plateforme, complete par
le referentiel des cultures. Aucune cle API ni connexion Internet n'est requise :
choix delibere, coherent avec la contrainte de budget nul du cahier des charges et
avec l'absence de connectivite fiable sur le terrain.
"""

import logging
import re
import threading

from django.core.cache import cache

from . import base_connaissances

logger = logging.getLogger('agria.assistant')

_verrou = threading.Lock()
_index = None  # (vectoriseur, matrice, liste_entrees) mis en cache en memoire de processus

SEUIL_SIMILARITE = 0.32

# TfidfVectorizer ne fournit pas de liste d'arret francaise native (seulement anglaise) ;
# sans elle, des mots grammaticaux tres frequents (comment, est, le...) faussent la
# similarite sur des messages courts et sans rapport avec la plateforme.
MOTS_VIDES_FRANCAIS = [
    "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "et", "ou", "a", "en",
    "est", "sont", "ete", "etre", "avoir", "ai", "as", "avez", "ont", "il", "elle", "ils",
    "elles", "je", "tu", "nous", "vous", "on", "mon", "ma", "mes", "ton", "ta", "tes", "son",
    "sa", "ses", "notre", "votre", "leur", "ce", "cet", "cette", "ces", "qui", "que", "quoi",
    "dont", "ou", "comment", "pourquoi", "quand", "combien", "quel", "quelle", "quels",
    "quelles", "pour", "par", "avec", "sans", "sur", "sous", "dans", "entre", "vers", "chez",
    "ne", "pas", "plus", "moins", "tres", "bien", "aussi", "donc", "si", "car", "mais",
    "ca", "cela", "y", "s", "l", "d", "n", "c", "j", "qu",
]


def _normaliser(texte):
    texte = texte.lower()
    texte = re.sub(r"[^a-z0-9àâäéèêëïîôöùûüç\s]", ' ', texte)
    return re.sub(r'\s+', ' ', texte).strip()


def _construire_index():
    from sklearn.feature_extraction.text import TfidfVectorizer

    entrees = []  # chaque entree : (texte_normalise, reponse, id)
    for item in base_connaissances.FAQ:
        for question in item['questions']:
            entrees.append((_normaliser(question), item['reponse'], item['id']))

    corpus = [texte for texte, _, _ in entrees]
    vectoriseur = TfidfVectorizer(stop_words=MOTS_VIDES_FRANCAIS)
    matrice = vectoriseur.fit_transform(corpus)
    return vectoriseur, matrice, entrees


def _obtenir_index():
    global _index
    if _index is None:
        with _verrou:
            if _index is None:
                _index = _construire_index()
    return _index


def _mots_significatifs(texte_normalise):
    return {mot for mot in texte_normalise.split() if mot not in MOTS_VIDES_FRANCAIS and len(mot) > 2}


def _rechercher_faq(message):
    from sklearn.metrics.pairwise import cosine_similarity

    vectoriseur, matrice, entrees = _obtenir_index()
    message_normalise = _normaliser(message)
    vecteur_requete = vectoriseur.transform([message_normalise])
    similarites = cosine_similarity(vecteur_requete, matrice)[0]
    meilleur_indice = similarites.argmax()
    meilleur_score = similarites[meilleur_indice]

    # Un score TF-IDF eleve peut provenir d'un seul mot rare partage entre deux phrases sans
    # rapport (corpus reduit). On exige donc au moins deux mots significatifs communs, sauf si
    # le score est tres eleve (correspondance quasi exacte sur une formulation courte).
    mots_requete = _mots_significatifs(message_normalise)
    mots_reference = _mots_significatifs(entrees[meilleur_indice][0])
    chevauchement = len(mots_requete & mots_reference)

    if meilleur_score >= SEUIL_SIMILARITE and (chevauchement >= 2 or meilleur_score >= 0.8):
        return entrees[meilleur_indice][1], meilleur_score
    return None, meilleur_score


def _rechercher_culture(message):
    """Repond directement si le message cite le nom d'une culture du referentiel."""
    from referentiel.models import Culture

    message_normalise = _normaliser(message)
    for culture in Culture.objects.all():
        if _normaliser(culture.nom) in message_normalise:
            return (
                f"{culture.nom} ({culture.nom_scientifique}) : pH ideal entre {culture.ph_min} et "
                f"{culture.ph_max}, cycle vegetatif d'environ {culture.cycle_jours} jours. "
                f"{culture.description}"
            )
    return None


SALUTATIONS = re.compile(
    r"^\s*(bonjour|bonsoir|salut|hello|coucou|hey|merci|bonne journee|au revoir|cc)\b.{0,15}$",
    re.IGNORECASE,
)
REPONSE_SALUTATION = (
    "Bonjour ! Je suis l'assistant AgriA. Posez-moi une question sur l'analyse de votre sol, "
    "les cultures, votre compte ou le fonctionnement de la plateforme."
)

REPONSE_INCONNUE = (
    "Je n'ai pas de reponse precise pour cette question dans ma base de connaissances actuelle. "
    "Essayez de reformuler, ou rapprochez-vous d'un Agent Vulgarisateur, d'un Expert Pedologue ou "
    "d'un administrateur de votre structure pour une reponse personnalisee."
)


def _cle_limite_debit(utilisateur_id):
    return f'assistant:limite:{utilisateur_id}'


def limite_atteinte(utilisateur):
    from django.conf import settings

    cle = _cle_limite_debit(utilisateur.pk)
    compte = cache.get(cle, 0)
    return compte >= settings.ASSISTANT_MAX_MESSAGES_PAR_HEURE


def enregistrer_appel(utilisateur):
    cle = _cle_limite_debit(utilisateur.pk)
    compte = cache.get(cle, 0)
    cache.set(cle, compte + 1, timeout=3600)


def obtenir_reponse(utilisateur, message, historique):
    """Recherche la meilleure reponse dans la base de connaissances locale.

    Le parametre historique est conserve pour compatibilite d'interface (utilise par la vue
    pour l'affichage), mais la recherche courante ne tient compte que du dernier message :
    une recherche documentaire n'a pas besoin de memoire conversationnelle complexe.
    """
    try:
        if SALUTATIONS.match(message.strip()):
            return REPONSE_SALUTATION

        reponse_culture = _rechercher_culture(message)
        if reponse_culture:
            return reponse_culture

        reponse_faq, score = _rechercher_faq(message)
        if reponse_faq:
            return reponse_faq

        logger.info('Assistant : aucune correspondance suffisante (score=%.2f) pour "%s"', score, message)
        return REPONSE_INCONNUE
    except Exception:
        logger.exception("Erreur inattendue dans l'assistant AgriA")
        return "Une erreur inattendue est survenue. Veuillez reessayer."
