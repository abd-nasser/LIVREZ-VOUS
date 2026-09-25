from django.db import models
from accounts_app.models import User
from commandes_app.models import Commande
from livreurs_app.models import Livreur


class AvisLivreur(models.Model):
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name='avis')  # un seul avis par commande
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_donnes')
    livreur = models.ForeignKey(Livreur, on_delete=models.CASCADE, related_name='avis')
    note = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    commentaire = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.note}/5 — {self.livreur}"