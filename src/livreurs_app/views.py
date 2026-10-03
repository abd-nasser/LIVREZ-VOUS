from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from livreurs_app.models import Livreur


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