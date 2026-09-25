from django.db import models
from django.urls import reverse

class Zone(models.Model):
    pays = models.CharField(max_length=100)
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ['pays', 'ville', 'quartier']
        ordering =  ['ville', 'quartier']
    

    
    
    def __str__(self):
        return f'{self.pays} ,{self.ville}-{self.quartier}'
    
