from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy

from livreurs_app.models import Livreur


from .forms import (InscriptionEntrepriseForm, 
                    InscriptionLivreurForm, 
                    InscriptionClientForm)



class CreateLivreurView(CreateView):
    form_class = InscriptionLivreurForm
    model = Livreur
    template_name = 'accounts_templates/livreurs_register.html'
    
    def form_valid(self, form):
        self.object = form.save()
        return render( self.request, 'partials/accounts/_livreurs_register_result.html',{
            'success':True,
            'Title' : "Bienvenue",
            'message':"Félicitation vous faites partie desormais de la plus grande communauté de livreur Neww gen du pays"
            
        })

