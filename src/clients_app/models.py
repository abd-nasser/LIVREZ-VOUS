from django.db import models

class Client(models.Model):
    user = models.OneToOneField('accounts_app.User', on_delete=models.CASCADE, related_name='client_profil')
    photo_profil = models.ImageField(upload_to='client_photos/', blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    quartier = models.CharField(max_length=100, blank=True, null=True)
    
    # Ajoutez d'autres champs spécifiques au client si nécessaire

    def __str__(self):
        return f"Client: {self.user.username}"
