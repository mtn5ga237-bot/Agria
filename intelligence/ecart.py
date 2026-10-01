"""Analyse d'ecart (gap analysis) entre les parametres d'un sol et les exigences d'une
culture cible choisie librement par le producteur - independamment de la culture recommandee
par le modele. Objectif : un agriculteur qui souhaite cultiver une culture precise (contrat
d'achat, tradition familiale...) voit ce qui manque a son sol et comment le corriger, plutot
que de se voir simplement repondre que cette culture n'est pas la mieux adaptee.

Les quantites d'intrants et les couts sont des estimations simplifiees, du meme ordre de
rigueur que le bareme de compatibilite du Tableau 16 : elles donnent un ordre de grandeur,
pas une prescription agronomique ou un devis. Les prix, notamment, varient fortement selon
la saison, la region et le fournisseur et doivent etre verifies localement.
"""

SEUIL_MATIERE_ORGANIQUE = 2.0  # %, seuil deja utilise par le bareme de score (Tableau 16)

# Prix indicatifs des intrants courants (FCFA/kg) : ordre de grandeur regional, a ajuster
# localement avant toute decision d'achat - ce ne sont pas des prix de marche verifies.
PRIX_INDICATIFS_FCFA_KG = {
    'Uree (46 % N)': 400,
    'Triple superphosphate (45 % P2O5)': 450,
    'Chlorure de potassium (60 % K2O)': 500,
    'Chaux agricole': 150,
    'Compost / fumure organique': 50,
}


def _ligne_intrant(parametre, intrant, deficit, teneur_intrant, delai):
    if deficit <= 0:
        return None
    quantite = round(deficit / teneur_intrant, 1)
    return {
        'parametre': parametre,
        'intrant': intrant,
        'quantite_kg_ha': quantite,
        'cout_estime_fcfa': round(quantite * PRIX_INDICATIFS_FCFA_KG[intrant]),
        'delai': delai,
    }


def analyser_ecart(culture_cible, parametres: dict, type_sol=None):
    """Compare `parametres` (le dict retourne par Analyse.parametres()) aux exigences de
    `culture_cible` et construit un plan d'amendement. Retourne un dictionnaire pret a
    afficher dans un gabarit."""

    ph = parametres.get('ph') or 0
    azote = parametres.get('azote') or 0
    phosphore = parametres.get('phosphore') or 0
    potassium = parametres.get('potassium') or 0
    matiere_organique = parametres.get('matiere_organique') or 0
    humidite = parametres.get('humidite')
    pluviometrie = parametres.get('pluviometrie')

    # --- Tableau comparatif parametre par parametre ------------------------------------
    ecarts = []

    if ph < culture_cible.ph_min:
        ecarts.append({'parametre': 'pH', 'mesure': ph, 'attendu': f'≥ {culture_cible.ph_min}', 'etat': 'deficit'})
    elif ph > culture_cible.ph_max:
        ecarts.append({'parametre': 'pH', 'mesure': ph, 'attendu': f'≤ {culture_cible.ph_max}', 'etat': 'exces'})
    else:
        ecarts.append({
            'parametre': 'pH', 'mesure': ph,
            'attendu': f'{culture_cible.ph_min} - {culture_cible.ph_max}', 'etat': 'conforme',
        })

    for label, mesure, besoin in [
        ('Azote (N)', azote, culture_cible.besoin_azote),
        ('Phosphore (P)', phosphore, culture_cible.besoin_phosphore),
        ('Potassium (K)', potassium, culture_cible.besoin_potassium),
    ]:
        ecarts.append({
            'parametre': label, 'mesure': mesure, 'attendu': f'≥ {besoin}',
            'etat': 'deficit' if mesure < besoin else 'conforme',
        })

    ecarts.append({
        'parametre': 'Matiere organique', 'mesure': matiere_organique,
        'attendu': f'≥ {SEUIL_MATIERE_ORGANIQUE} %',
        'etat': 'deficit' if matiere_organique < SEUIL_MATIERE_ORGANIQUE else 'conforme',
    })

    if type_sol is not None:
        compatible = culture_cible.sols_favorables.filter(pk=type_sol.pk).exists()
        ecarts.append({
            'parametre': 'Type de sol', 'mesure': type_sol.libelle,
            'attendu': 'figure parmi les sols favorables', 'etat': 'conforme' if compatible else 'exces',
        })

    # Facteurs climatiques : informatifs uniquement, aucun intrant ne les corrige.
    for label, valeur in [('Humidite relative', humidite), ('Pluviometrie', pluviometrie)]:
        if valeur is not None:
            ecarts.append({
                'parametre': label, 'mesure': valeur,
                'attendu': 'facteur climatique (non amendable)', 'etat': 'climat',
            })

    # --- Plan d'amendement (parametres du sol reellement corrigibles) ------------------
    plan = []

    if ph < culture_cible.ph_min:
        deficit_ph = culture_cible.ph_min - ph
        # Estimation grossiere : environ 1 t/ha de chaux agricole pour relever le pH d'un point.
        quantite = round(deficit_ph * 1000)
        plan.append({
            'parametre': 'pH (sol trop acide)', 'intrant': 'Chaux agricole',
            'quantite_kg_ha': quantite,
            'cout_estime_fcfa': round(quantite * PRIX_INDICATIFS_FCFA_KG['Chaux agricole']),
            'delai': "a epandre 4 a 6 semaines avant le semis (action lente)",
        })
    elif ph > culture_cible.ph_max:
        plan.append({
            'parametre': 'pH (sol trop basique)', 'intrant': 'Matiere organique acidifiante (compost, soufre)',
            'quantite_kg_ha': None, 'cout_estime_fcfa': None,
            'delai': 'correction progressive sur plusieurs saisons',
        })

    for ligne in [
        _ligne_intrant('Azote (N)', 'Uree (46 % N)', culture_cible.besoin_azote - azote, 0.46,
                        'a epandre en couverture pres du semis'),
        _ligne_intrant('Phosphore (P)', 'Triple superphosphate (45 % P2O5)',
                        culture_cible.besoin_phosphore - phosphore, 0.45,
                        'a epandre 2 a 3 semaines avant le semis'),
        _ligne_intrant('Potassium (K)', 'Chlorure de potassium (60 % K2O)',
                        culture_cible.besoin_potassium - potassium, 0.60,
                        'a epandre 2 a 3 semaines avant le semis'),
    ]:
        if ligne:
            plan.append(ligne)

    if matiere_organique < SEUIL_MATIERE_ORGANIQUE:
        deficit_mo = SEUIL_MATIERE_ORGANIQUE - matiere_organique
        # Estimation grossiere : environ 5 t/ha de compost pour +0,5 point de matiere organique.
        quantite = round(deficit_mo * 5000 / 0.5)
        plan.append({
            'parametre': 'Matiere organique', 'intrant': 'Compost / fumure organique',
            'quantite_kg_ha': quantite,
            'cout_estime_fcfa': round(quantite * PRIX_INDICATIFS_FCFA_KG['Compost / fumure organique']),
            'delai': "a incorporer 3 a 4 semaines avant le semis",
        })

    cout_total = sum(l['cout_estime_fcfa'] for l in plan if l.get('cout_estime_fcfa'))

    # --- Score actuel et score simule apres application du plan ------------------------
    score_actuel = culture_cible.calculer_score(type_sol, parametres)

    parametres_simules = dict(parametres)
    parametres_simules['ph'] = min(max(ph, culture_cible.ph_min), culture_cible.ph_max)
    parametres_simules['azote'] = max(azote, culture_cible.besoin_azote)
    parametres_simules['phosphore'] = max(phosphore, culture_cible.besoin_phosphore)
    parametres_simules['potassium'] = max(potassium, culture_cible.besoin_potassium)
    parametres_simules['matiere_organique'] = max(matiere_organique, SEUIL_MATIERE_ORGANIQUE)
    score_simule = culture_cible.calculer_score(type_sol, parametres_simules)

    if score_actuel >= 70:
        faisabilite = 'immediate'
    elif score_simule >= 40:
        faisabilite = 'avec_amendements'
    else:
        faisabilite = 'non_recommandee'

    return {
        'culture': culture_cible,
        'ecarts': ecarts,
        'plan_amendement': plan,
        'cout_total_estime_fcfa': cout_total,
        'score_actuel': score_actuel,
        'score_simule': score_simule,
        'faisabilite': faisabilite,
    }
