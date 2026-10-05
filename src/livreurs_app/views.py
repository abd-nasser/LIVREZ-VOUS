from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from livreurs_app.models import Livreur


class ListLivreursView(LoginRequiredMixin, ListView):
    model = Livreur
    context_object_name = 'livreurs'
    paginate_by = 12  # Pagination recommandée pour les grilles HTMX
    
    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            return ['partials/livreurs/_livreurs_list.html']
        return ['livreurs_templates/livreurs_list.html']
        
    def get_queryset(self):
        # Base QuerySet optimisé avec select_related pour éviter les requêtes N+1
        qs = Livreur.objects.select_related('user', 'zone_actuelle').all()

        # 1. Filtre par disponibilité
        if self.request.GET.get('disponible') == 'true':
            qs = qs.filter(disponible=True)
            
        # 2. Filtre manuel par Ville / Quartier (Requête GET)
        ville = self.request.GET.get('ville')
        quartier = self.request.GET.get('quartier')
        
        if ville:
            qs = qs.filter(zone_actuelle__ville__icontains=ville)
        if quartier:
            qs = qs.filter(zone_actuelle__quartier__icontains=quartier)

        # 3. Fallback : Si aucun paramètre manuel n'est fourni, on applique la zone de l'utilisateur
        if not (ville or quartier):
            client_profile = getattr(self.request.user, 'client_profile', None)
            if client_profile and client_profile.ville and client_profile.quartier:
                qs = qs.filter(
                    zone_actuelle__ville=client_profile.ville,
                    zone_actuelle__quartier=client_profile.quartier
                )

        # 4. Recherche texte (Nom, Prénom, Téléphone)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            qs = qs.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__telephone__icontains=search_query)
            )

        return qs.order_by('-disponible', 'user__first_name')

class LivreurProfileView(LoginRequiredMixin, DetailView):
    model = Livreur
    context_object_name = 'livreur'
    
    def get_template_names(self):
        if self.request.user.role == 'livreur':
            return ['livreurs_templates/livreur_profile.html']
        return ['livreurs_templates/client_livreur_profile.html']
    
def disponibilite_livreur(request, pk):
    livreur = get_object_or_404(Livreur, pk=pk)
    
    if request.method == 'POST':
        livreur.disponible = not livreur.disponible
        livreur.save()

    return render(
        request, 
        'partials/livreurs/_livreur_disponibilite_status.html', 
        {'livreur': livreur}
    )
    
    