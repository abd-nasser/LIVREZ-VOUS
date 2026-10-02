from django.shortcuts import render
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from livreurs_app.models import Livreur


class LivreurProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Livreur
    context_object_name = 'livreur'
    
    def get_template_names(self):
        if self.request.user.role == 'livreur':
            return ['livreurs_templates/livreur_profile.html']
        return ['livreurs_templates/client_livreur_profile.html']
    
