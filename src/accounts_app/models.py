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
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    # Un identifiant unique pour la connexion par téléphone
    telephone = models.CharField(max_length=20, unique=True, verbose_name="Numéro de téléphone")
    
    last_activity = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    # ---------------- CONFIGURATION POUR DJANGO ----------------------
    USERNAME_FIELD = "telephone"  # Le téléphone est l'identifiant principal

    def __str__(self):
        return f"{self.get_full_name() or self.username or self.telephone} ({self.get_role_display()})"