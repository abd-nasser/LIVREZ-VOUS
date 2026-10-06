from django.shortcuts import render
from django.views.generic import DetailView
from .models import Entreprise


class EntrepriseProfilView(DetailView):
    model = Entreprise
    context_object_name = 'entreprise'
    def get_template_names(self):
        if self.request.user.is_authenticated and self.request.user == self.object.user_principal:
            return ['entreprises_templates/entreprise_admin_profil.html']
        
        return ['entreprises_templates/entreprise_profil.html']


