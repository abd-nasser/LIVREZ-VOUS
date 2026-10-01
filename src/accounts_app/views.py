from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from livreurs_app.models import Livreur


from .forms import (InscriptionEntrepriseForm, 
                    InscriptionLivreurForm, 
                    InscriptionClientForm)



class CreateLivreurView(CreateView):
    form_class = InscriptionLivreurForm
    model = Livreur
    template_name = 'accounts_templates/livreurs_register.html'
    
   

    def form_valid(self, form):
        # En cas de SUCCÈS : HTMX remplace le conteneur global par le toast de succès
        return render(self.request, 'partials/accounts/_livreurs_register_result.html', {
            'success': True,
            'Title': "Bienvenue",
            'message': "Félicitations, vous faites désormais partie de la plus grande communauté de livreurs !"
        })

    def form_invalid(self, form):
        # En cas d'ERREUR : On renvoie le formulaire avec ses erreurs
        response = render(self.request, 'partials/accounts/_livreurs_register_error_form.html', {
            'inscription_livreur_form_errors': form, # Ton formulaire avec ses erreurs nettoyées
        })
        # ON RETARGET SUR LE BLOC FORMULAIRE SEULEMENT ET ON SWAP LE CONTENU
        response['HX-Retarget'] = '#form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response