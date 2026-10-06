from django.db import models
from accounts_app.models import User
from zones_app.models import Zone

class Entreprise(models.Model):
    PALIER_CHOICES = [
        ('pas_defini', 'Pas defini'),
        ('standard', 'Standard'),
        ('pro', 'Pro'),
        ('premium', "Premium")
    ]
    
    user_principal = models.OneToOneField(User, on_delete=models.CASCADE, related_name='entreprise_profil')
    nom_entreprise = models.CharField(max_length=150)
    logo = models.ImageField(upload_to='entreprises/logos', null=True, blank=True)
    zones_couvertes = models.ManyToManyField(Zone, related_name='entreprises', blank=True)
    palier = models.CharField(max_length=20, choices=PALIER_CHOICES, default='pas_defini')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    QUOTAS_LIVREURS = {
        'standard': 5,
        'pro': 20,
        'premium': 999
    }
    
    QUOTAS_ADMINS = {
        'standard': 1,
        'pro': 3,
        'premium':10
    }
    
    @property
    def quota_livreurs(self):
        return self.QUOTAS_LIVREURS.get(self.palier, 0)
    
    @property
    def quota_admins(self):
        return self.QUOTAS_ADMINS.get(self.palier, 0)
    
    @property
    def nb_livreurs_actuels(self):
        return self.livreurs.filter(actif=True).count()
    
    @property 
    def nb_admins_actuels(self):
        return self.membres_admin.count()
    
    @property
    def peut_ajouter_livreur(self):
        return self.nb_livreurs_actuels < self.quota_livreurs
    
    @property
    def peut_ajouter_admin(self):
        return self.nb_admins_actuels < self.quota_admins
    
    def __str__(self):
        return self.nom_entreprise
    
   
    
class MembreAdminsEntreprise(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='membres_admin')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='membre_admin_profil')
    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admins_ajoutes')
    
    def __str__(self):
        return f"{self.user.get_full_name()} — admin {self.entreprise.nom_entreprise}"
    