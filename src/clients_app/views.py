from django.shortcuts import render
from django.views.generic import DetailView
from .models import Client

class ClientProfileView(DetailView):
    model = Client
    template_name = 'clients_templates/client_profile.html'
    context_object_name = 'client'
