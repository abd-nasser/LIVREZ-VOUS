import logging

from django.contrib.auth import authenticate, login, logout as auth_logout
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.views.generic import CreateView
from clients_app.models import Client
from livreurs_app.models import Livreur
from entreprises_app.models import Entreprise
from .models import User
from django.contrib.auth.decorators import login_required   

from .forms import (InscriptionEntrepriseForm, 
                    InscriptionLivreurForm, 
                    InscriptionClientForm)


logger = logging.getLogger(__name__)

class CreateEntrepriseView(CreateView):
    form_class = InscriptionEntrepriseForm
    model = Entreprise
    template_name = 'accounts_templates/entreprises_register.html'
    
    def form_valid(self, form):
        with transaction.atomic():
            try:# Assure que la création de l'utilisateur et du profil Entreprise est atomique
                form.save()  # Sauvegarde le formulaire et crée l'utilisateur + le profil Entreprise
                # En cas de SUCCÈS : HTMX remplace le conteneur global par le toast de succès
                response = render(self.request, 'partials/accounts/_entreprises_register_result.html', {
                    'success': True,
                    'Title': "Bienvenue",
                    'message': "Félicitations, vous faites désormais partie de la plus grande communauté d'entreprises !"
                })
                response['HX-Trigger'] = 'entreprise-register-success'
                return response
            except Exception as e:
                # En cas d'ERREUR : On renvoie le formulaire avec ses erreurs
                logger.error(f"Erreur lors de la création de l'entreprise : {e}")
                response = render(self.request, 'partials/accounts/_entreprises_register_error_form.html', {
                    'inscription_entreprise_form_errors': form, # Ton formulaire avec ses erreurs nettoyées
                })
                # ON RETARGET SUR LE BLOC FORMULAIRE SEULEMENT ET ON SWAP LE CONTENU
                response['HX-Retarget'] = '#form-container'
                response['HX-Reswap'] = 'innerHTML'
                return response

    def form_invalid(self, form):
        # En cas d'ERREUR : On renvoie le formulaire avec ses erreurs
        response = render(self.request, 'partials/accounts/_entreprises_register_error_form.html', {
            'inscription_entreprise_form_errors': form, # Ton formulaire avec ses erreurs nettoyées
        })
        # ON RETARGET SUR LE BLOC FORMULAIRE SEULEMENT ET ON SWAP LE CONTENU
        response['HX-Retarget'] = '#form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response

class CreateLivreurView(CreateView):
    form_class = InscriptionLivreurForm
    model = Livreur
    template_name = 'accounts_templates/livreurs_register.html'
    
    def form_valid(self, form):
        form.save()  # Sauvegarde le formulaire et crée l'utilisateur + le profil Livreur
        # En cas de SUCCÈS : HTMX remplace le conteneur global par le toast de succès
        response = render(self.request, 'partials/accounts/_livreurs_register_result.html', {
            'success': True,
            'Title': "Bienvenue",
            'message': "Félicitations, vous faites désormais partie de la plus grande communauté de livreurs !"
        })
        response['HX-Trigger'] = 'livreur-register-success'
        return response

    def form_invalid(self, form):
        # En cas d'ERREUR : On renvoie le formulaire avec ses erreurs
        response = render(self.request, 'partials/accounts/_livreurs_register_error_form.html', {
            'inscription_livreur_form_errors': form, # Ton formulaire avec ses erreurs nettoyées
        })
        # ON RETARGET SUR LE BLOC FORMULAIRE SEULEMENT ET ON SWAP LE CONTENU
        response['HX-Retarget'] = '#form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response
    
class CreateClientView(CreateView):
    form_class = InscriptionClientForm
    model = Client
    template_name = 'accounts_templates/clients_register.html'
    
    def form_valid(self, form):
        form.save()
        response = render(self.request, 'partials/accounts/_clients_register_result.html', {
            'success': True,
            'Title': "Bienvenue",
            'message': "Félicitations, vous faites désormais partie de la plus grande communauté de clients !"
        })
        response['HX-Trigger'] = 'client-register-success'
        return response

    def form_invalid(self, form):
        # En cas d'ERREUR : On renvoie le formulaire avec ses erreurs
        response = render(self.request, 'partials/accounts/_clients_register_error_form.html', {
            'inscription_client_form_errors': form, # Ton formulaire avec ses erreurs nettoyées
        })
        # ON RETARGET SUR LE BLOC FORMULAIRE SEULEMENT ET ON SWAP LE CONTENU
        response['HX-Retarget'] = '#form-container'
        response['HX-Reswap'] = 'innerHTML'
        return response


def login_view(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    login_method = request.POST.get('login_method')
    identifier = request.POST.get(login_method, '').strip() if login_method in {'username', 'telephone'} else ''
    user_record = None
    if identifier:
        user_record = User.objects.filter(**{login_method: identifier}).first()

    user = None
    if user_record:
        user = authenticate(request, username=user_record.telephone, password=request.POST.get('password', ''))

    if user is None:
        response = render(request, 'partials/accounts/_login_message.html', {
            'success': False,
            'message': "Identifiant ou mot de passe incorrect.",
        })
        response['HX-Retarget'] = '#login-message'
        response['HX-Reswap'] = 'innerHTML'
        return response

    login(request, user)
    response = render(request, 'partials/accounts/_login_message.html', {
        'success': True,
        'message': f"Bienvenue {user.first_name} !",
        'reload_on_close' :True,
    })
    response['HX-Trigger'] = 'login-success'
    return response


def logout_view(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    auth_logout(request)
    return redirect('home_app:home-page')