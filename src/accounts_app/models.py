from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('livreur', 'Livreur'),
        ('entreprise', 'Entreprise de livraison'),
        ('staff', 'Équipe interne'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
  
    
    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'