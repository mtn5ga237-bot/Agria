"""Moteur de recommandation de cultures (CropRecommender, Annexe 6d ; Tableau 16)."""

from referentiel.models import Culture, TypeSol


class CropRecommender:
    SEUIL = 40
    LIMITE_PAR_DEFAUT = 6

    def recommander(self, type_sol: TypeSol | None, parametres: dict, limite: int = LIMITE_PAR_DEFAUT):
        resultats = []
        for culture in Culture.objects.prefetch_related('sols_favorables'):
            score = culture.calculer_score(type_sol, parametres)
            if score >= self.SEUIL:
                resultats.append({'culture': culture, 'score': score})

        resultats.sort(key=lambda r: r['score'], reverse=True)
        for rang, resultat in enumerate(resultats[:limite], start=1):
            resultat['rang'] = rang
        return resultats[:limite]
