import csv
import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from comptes.middleware import adresse_ip_client
from comptes.models import JournalActivite
from intelligence.image_predictor import SoilImagePredictor
from intelligence.predictor import SoilPredictor
from intelligence.recommender import CropRecommender
from referentiel.models import Culture, TypeSol

from .forms import FormulaireAnalyse
from .models import Analyse, Recommandation

logger = logging.getLogger('agria.securite')


class LancerAnalyseView(LoginRequiredMixin, View):
    """Vue centrale d'AgriA : saisie des parametres, prediction, recommandation (Figure 9).

    Deux predictions independantes et complementaires :
    - la culture la mieux adaptee, a partir des parametres physico-chimiques (Random Forest,
      Crop Recommendation Dataset) ;
    - le type de sol reel, a partir d'une photographie facultative (classificateur d'image).
    Lorsque les deux sont disponibles, le moteur de recommandation combine les deux pour affiner
    le score de compatibilite de chaque culture (Tableau 16).
    """

    template_name = 'analyses/formulaire.html'

    def get(self, request):
        form = FormulaireAnalyse(request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = FormulaireAnalyse(request.user, request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        analyse = form.save(commit=False)
        analyse.operateur = request.user
        analyse.statut = Analyse.Statut.EN_COURS
        analyse.save()

        try:
            resultat_culture = SoilPredictor().predire({
                'azote': analyse.azote, 'phosphore': analyse.phosphore, 'potassium': analyse.potassium,
                'ph': analyse.ph, 'temperature': analyse.temperature,
                'humidite': analyse.humidite, 'pluviometrie': analyse.pluviometrie,
            })
        except Exception:
            analyse.statut = Analyse.Statut.ERREUR
            analyse.save(update_fields=['statut'])
            logger.exception("Echec de la prediction pour l'analyse %s", analyse.pk)
            messages.error(request, "La prediction a echoue. Veuillez reessayer ou contacter un administrateur.")
            return redirect('analyses:historique')

        # Les classes du modele proviennent du meme jeu de donnees que le referentiel des
        # cultures : chaque code predit doit donc y correspondre exactement.
        analyse.culture_predite = Culture.objects.get(code=resultat_culture['nom_culture'])
        analyse.confiance_culture = resultat_culture['confiance']
        analyse.importances_variables = resultat_culture['importances']

        type_sol = None
        if analyse.photo_sol:
            try:
                resultat_sol = SoilImagePredictor().predire(analyse.photo_sol)
                type_sol = TypeSol.objects.filter(code=resultat_sol['code_type_sol']).first()
                analyse.type_sol = type_sol
                analyse.confiance_sol = resultat_sol['confiance']
            except Exception:
                logger.exception("Echec de la classification d'image pour l'analyse %s", analyse.pk)
                messages.warning(request, "La photo n'a pas pu etre analysee ; la culture recommandee reste disponible.")

        analyse.validee = resultat_culture['fiable']
        analyse.statut = Analyse.Statut.TERMINEE
        analyse.save()

        recommandations = CropRecommender().recommander(type_sol, analyse.parametres())
        Recommandation.objects.bulk_create([
            Recommandation(analyse=analyse, culture=r['culture'], score=r['score'], rang=r['rang'])
            for r in recommandations
        ])

        if not resultat_culture['fiable']:
            messages.warning(
                request,
                f"Indice de confiance de {resultat_culture['confiance']:.0f} % (inferieur au seuil de 70 %) : "
                "cette analyse est signalee pour validation par un expert pedologue.",
            )
        return redirect('analyses:resultat', pk=analyse.pk)


class ResultatAnalyseView(LoginRequiredMixin, DetailView):
    model = Analyse
    template_name = 'analyses/resultat.html'
    context_object_name = 'analyse'

    def get_queryset(self):
        qs = Analyse.objects.select_related(
            'parcelle', 'type_sol', 'culture_predite',
        ).prefetch_related('recommandations__culture')
        utilisateur = self.request.user
        if utilisateur.a_le_role('expert', 'admin'):
            return qs
        if utilisateur.a_le_role('agent'):
            return qs.filter(Q(parcelle__proprietaire=utilisateur) | Q(operateur=utilisateur))
        return qs.filter(parcelle__proprietaire=utilisateur)

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        if self.request.user.a_le_role('expert', 'admin'):
            contexte['cultures'] = Culture.objects.order_by('nom')
            contexte['types_sols'] = TypeSol.objects.order_by('libelle')
        return contexte


class HistoriqueAnalysesView(LoginRequiredMixin, ListView):
    template_name = 'analyses/historique.html'
    context_object_name = 'analyses'
    paginate_by = 20

    def get_queryset(self):
        qs = Analyse.objects.select_related('parcelle', 'type_sol', 'culture_predite')
        if self.request.user.a_le_role('agent'):
            return qs.filter(operateur=self.request.user)
        if self.request.user.a_le_role('expert', 'admin'):
            return qs
        return qs.filter(parcelle__proprietaire=self.request.user)


class ValiderAnalyseView(LoginRequiredMixin, View):
    """Permet a un expert pedologue de valider ou corriger une prediction (Tableau 4).

    Le formulaire de la page de resultat propose toujours les listes deroulantes de la
    culture et du type de sol (preselectionnees sur la prediction courante) : l'expert peut
    donc soit confirmer tel quel, soit choisir une autre valeur avant de valider.
    """

    def post(self, request, pk):
        if not request.user.a_le_role('expert', 'admin'):
            messages.error(request, "Seul un expert pedologue peut valider une analyse.")
            return redirect('analyses:resultat', pk=pk)
        analyse = get_object_or_404(Analyse, pk=pk)
        correction_apportee = False

        code_culture = request.POST.get('culture')
        if code_culture:
            nouvelle_culture = get_object_or_404(Culture, code=code_culture)
            if nouvelle_culture.pk != analyse.culture_predite_id:
                correction_apportee = True
            analyse.culture_predite = nouvelle_culture

        code_type_sol = request.POST.get('type_sol', '')
        nouveau_type_sol = TypeSol.objects.filter(code=code_type_sol).first() if code_type_sol else None
        if nouveau_type_sol != analyse.type_sol:
            correction_apportee = True
        analyse.type_sol = nouveau_type_sol

        if correction_apportee:
            # Une correction manuelle d'un expert est une verite de terrain : la confiance est maximale.
            analyse.confiance_culture = 100.0

        analyse.validee = True
        analyse.save(update_fields=['validee', 'type_sol', 'culture_predite', 'confiance_culture'])

        JournalActivite.objects.create(
            utilisateur=request.user,
            action=f"{'Correction et validation' if correction_apportee else 'Validation'} de l'analyse #{analyse.pk}",
            adresse_ip=adresse_ip_client(request),
        )
        messages.success(
            request,
            'Analyse corrigee et validee.' if correction_apportee else 'Prediction confirmee et validee.',
        )
        return redirect('analyses:resultat', pk=pk)


def exporter_historique_view(request, format_export):
    if not request.user.is_authenticated:
        return redirect('comptes:connexion')

    qs = Analyse.objects.select_related('parcelle', 'type_sol', 'culture_predite')
    if request.user.a_le_role('agent'):
        qs = qs.filter(operateur=request.user)
    elif request.user.a_le_role('expert', 'admin'):
        pass
    else:
        qs = qs.filter(parcelle__proprietaire=request.user)
    lignes = [{
        'date': a.date_analyse.isoformat(),
        'parcelle': a.parcelle.nom,
        'culture_recommandee': a.culture_predite.nom if a.culture_predite else '',
        'type_sol': a.type_sol.libelle if a.type_sol else '',
        'ph': a.ph,
        'confiance': a.confiance_culture,
    } for a in qs]

    if format_export == 'json':
        reponse = HttpResponse(json.dumps(lignes, ensure_ascii=False, indent=2), content_type='application/json')
        reponse['Content-Disposition'] = 'attachment; filename="historique_agria.json"'
        return reponse

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment; filename="historique_agria.csv"'
    ecrivain = csv.DictWriter(
        reponse, fieldnames=['date', 'parcelle', 'culture_recommandee', 'type_sol', 'ph', 'confiance'],
    )
    ecrivain.writeheader()
    ecrivain.writerows(lignes)
    return reponse
