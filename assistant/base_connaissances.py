"""Base de connaissances statique de l'assistant AgriA.

Chaque entree associe une ou plusieurs formulations possibles d'une question a une
reponse redigee en francais simple, couvrant le guide d'utilisateur, le glossaire et
le fonctionnement technique decrits dans le rapport de stage (Dossier VII notamment).
Cette base alimente une recherche par similarite (TF-IDF) : aucune cle API ni
connexion Internet n'est necessaire, conformement a la contrainte de budget nul.
"""

FAQ = [
    {
        "id": "presentation",
        "questions": [
            "Qu'est-ce qu'AgriA", "A quoi sert cette plateforme", "Presentation d'AgriA",
        ],
        "reponse": (
            "AgriA est une plateforme web d'analyse et de classification des sols assistee par "
            "Intelligence Artificielle, developpee pour aider les agriculteurs du Nord-Cameroun a "
            "choisir les cultures les mieux adaptees a leurs parcelles. Vous renseignez quelques "
            "parametres simples de votre sol (pH, azote, phosphore, potassium, temperature, "
            "humidite, pluviometrie), et un modele d'apprentissage automatique identifie la culture "
            "la plus adaptee, avec un indice de confiance et des recommandations classees par score."
        ),
    },
    {
        "id": "analyse_comment",
        "questions": [
            "Comment analyser mon sol", "Comment faire une analyse", "Comment lancer une analyse",
            "Ou saisir les parametres du sol",
        ],
        "reponse": (
            "Depuis le menu « Analyser mon sol », choisissez une parcelle (ou creez-en une), puis "
            "renseignez le pH, l'azote (N), le phosphore (P), le potassium (K), la temperature, "
            "l'humidite relative et la pluviometrie annuelle. Cliquez sur « Lancer l'analyse » : le "
            "resultat s'affiche en moins de deux secondes, avec le type de sol identifie et les "
            "cultures recommandees."
        ),
    },
    {
        "id": "indice_confiance",
        "questions": [
            "Qu'est-ce que l'indice de confiance", "Que signifie la confiance de la prediction",
            "Pourquoi mon analyse est en attente de validation", "Confiance faible",
        ],
        "reponse": (
            "L'indice de confiance correspond a la proportion des arbres de la foret aleatoire "
            "(Random Forest) ayant vote pour la culture predite : plus il est eleve, plus la "
            "prediction est fiable. En dessous de 70 %, l'analyse est automatiquement signalee pour "
            "verification par un expert pedologue, qui peut confirmer ou corriger le resultat."
        ),
    },
    {
        "id": "score_recommandation",
        "questions": [
            "Comment est calcule le score de compatibilite", "Bareme de recommandation des cultures",
            "Pourquoi cette culture est recommandee",
        ],
        "reponse": (
            "Chaque culture recoit un score sur 100 : 40 points si le type de sol identifie fait "
            "partie de ses sols favorables, 30 points si le pH mesure est dans sa plage de "
            "tolerance, 15 points si la matiere organique atteint au moins 2 %, et 5 points chacun "
            "pour l'azote, le phosphore et le potassium si les seuils requis sont atteints. Seules "
            "les cultures avec un score d'au moins 40 sont affichees, classees par ordre decroissant."
        ),
    },
    {
        "id": "roles",
        "questions": [
            "Quels sont les roles disponibles", "Difference entre agriculteur agent et expert",
            "Que peut faire un administrateur",
        ],
        "reponse": (
            "AgriA propose quatre profils : l'Agriculteur analyse ses propres parcelles ; l'Agent "
            "Vulgarisateur realise des analyses pour le compte des producteurs qu'il encadre ; "
            "l'Expert Pedologue valide les analyses a faible confiance, gere le referentiel des sols "
            "et declenche le reentrainement du modele ; l'Administrateur gere les comptes "
            "utilisateurs et le referentiel des cultures."
        ),
    },
    {
        "id": "compte_inactif",
        "questions": [
            "Pourquoi je ne peux pas me connecter", "Mon compte est inactif",
            "Combien de temps pour activer mon compte",
        ],
        "reponse": (
            "Un compte nouvellement cree est inactif par defaut : il doit etre active par un "
            "administrateur avant la premiere connexion. Si votre inscription date de plus de "
            "quelques heures et que vous ne pouvez toujours pas vous connecter, contactez un "
            "administrateur de votre structure."
        ),
    },
    {
        "id": "mot_de_passe_oublie",
        "questions": [
            "J'ai oublie mon mot de passe", "Comment reinitialiser mon mot de passe",
            "Reinitialisation de mot de passe",
        ],
        "reponse": (
            "Cliquez sur « Mot de passe oublie ? » depuis la page de connexion, saisissez votre "
            "adresse electronique : si elle correspond a un compte actif, un lien de "
            "reinitialisation valable deux heures vous sera envoye par email. Ce lien est a usage "
            "unique."
        ),
    },
    {
        "id": "securite",
        "questions": [
            "Comment mes donnees sont-elles protegees", "Securite de la plateforme",
            "Mots de passe sont-ils visibles", "Pourquoi mon compte est verrouille",
            "Compte bloque apres plusieurs tentatives", "Mon compte est bloque",
        ],
        "reponse": (
            "Les mots de passe sont hache's avec l'algorithme PBKDF2 (600 000 iterations) et ne "
            "sont jamais stockes en clair. La plateforme protege contre les attaques CSRF, les "
            "injections SQL (via l'ORM Django) et les injections de script (XSS). Apres cinq echecs "
            "de connexion, un compte est temporairement verrouille. Chaque operation sensible est "
            "journalisee."
        ),
    },
    {
        "id": "carte",
        "questions": [
            "Comment fonctionne la carte", "Voir mes parcelles sur la carte",
            "Couleur des marqueurs sur la carte",
        ],
        "reponse": (
            "La rubrique « Carte » affiche toutes vos parcelles analysees sur un fond "
            "OpenStreetMap centre sur Garoua. La couleur de chaque marqueur correspond au type de "
            "sol identifie ; cliquez sur un marqueur pour voir la date, le type de sol et les "
            "principales cultures recommandees."
        ),
    },
    {
        "id": "historique_export",
        "questions": [
            "Comment exporter mon historique", "Telecharger mes analyses",
            "Historique des analyses",
        ],
        "reponse": (
            "La rubrique « Historique » liste toutes vos analyses passees. Deux boutons en haut de "
            "la page permettent d'exporter vos donnees au format CSV ou JSON."
        ),
    },
    {
        "id": "reentrainement",
        "questions": [
            "Comment reentrainer le modele", "A quoi sert le reentrainement",
            "Le modele s'ameliore-t-il avec le temps",
        ],
        "reponse": (
            "Un expert pedologue peut declencher le reentrainement depuis « Reentrainer le "
            "modele ». Le systeme fusionne les analyses validees par les experts au jeu de donnees "
            "d'origine, entraine un nouveau modele, l'evalue, puis ne l'active en production que si "
            "son exactitude est superieure a celle du modele courant ; sinon, il est simplement "
            "archive."
        ),
    },
    {
        "id": "parametres_signification",
        "questions": [
            "Que signifie NPK", "C'est quoi le pH du sol", "C'est quoi la matiere organique",
            "Difference azote phosphore potassium",
        ],
        "reponse": (
            "N, P et K designent respectivement l'azote, le phosphore et le potassium, trois "
            "elements nutritifs essentiels a la croissance des plantes, mesures en mg/kg. Le pH "
            "indique l'acidite ou l'alcalinite du sol sur une echelle de 0 a 14 (7 = neutre). La "
            "matiere organique correspond aux debris vegetaux et animaux en decomposition, qui "
            "determinent en grande partie la fertilite du sol."
        ),
    },
    {
        "id": "modele_ia",
        "questions": [
            "Quel algorithme d'IA est utilise", "Comment fonctionne le modele",
            "Pourquoi Random Forest",
        ],
        "reponse": (
            "AgriA utilise deux modeles complementaires, tous deux des forets d'arbres decisionnels "
            "(Random Forest, scikit-learn) : le premier predit la culture la mieux adaptee a partir "
            "des parametres physico-chimiques (2200 observations, 22 cultures) ; le second identifie "
            "le type de sol reel a partir d'une photographie (couleur et texture, 7 types de sols, "
            "pres de 5100 images d'entrainement). Cet algorithme a ete choisi pour son explicabilite, "
            "sa robustesse au surapprentissage et son faible cout de calcul, adapte a une connexion "
            "Internet parfois limitee."
        ),
    },
    {
        "id": "classification_sol_photo",
        "questions": [
            "Comment identifier le vrai type de sol", "Classification du sol par photo",
            "Difference entre type de sol et culture recommandee", "A quoi sert la photo du sol",
        ],
        "reponse": (
            "Il y a deux predictions distinctes dans AgriA : la « culture recommandee » (Coton, Riz...) "
            "vient des parametres physico-chimiques saisis (pH, N, P, K, climat). Le « type de sol » "
            "reel (Alluvial, Noir, Lateritique, Aride, Montagne, Rouge ou Jaune) est identifie "
            "uniquement si vous ajoutez une photo de votre sol lors de l'analyse : un second modele, "
            "entraine sur des milliers d'images, reconnait le type de sol a partir de sa couleur et de "
            "sa texture. Ajouter une photo affine aussi les scores de compatibilite des cultures."
        ),
    },
    {
        "id": "parcelle_creation",
        "questions": [
            "Comment ajouter une parcelle", "Creer une nouvelle parcelle",
            "Comment positionner ma parcelle sur la carte",
        ],
        "reponse": (
            "Depuis « Mes parcelles », cliquez sur « Nouvelle parcelle », renseignez son nom, sa "
            "superficie et sa localite, puis indiquez ses coordonnees soit en cliquant directement "
            "sur la carte, soit via le bouton de geolocalisation."
        ),
    },
    {
        "id": "contact_humain",
        "questions": [
            "Je veux parler a un humain", "Comment contacter un administrateur",
            "Cet assistant ne peut pas m'aider",
        ],
        "reponse": (
            "Pour toute question depassant le fonctionnement de la plateforme, rapprochez-vous "
            "d'un Agent Vulgarisateur ou d'un Expert Pedologue de votre structure, ou d'un "
            "administrateur pour les problemes de compte."
        ),
    },
]


def contexte_cultures():
    """Genere un resume du referentiel des cultures pour enrichir les reponses agronomiques."""
    from referentiel.models import Culture

    lignes = []
    for culture in Culture.objects.all().order_by('nom'):
        lignes.append(
            f"{culture.nom} ({culture.nom_scientifique}) : pH ideal entre {culture.ph_min} et "
            f"{culture.ph_max}, cycle vegetatif d'environ {culture.cycle_jours} jours, "
            f"besoin en azote autour de {culture.besoin_azote} mg/kg."
        )
    return lignes
