from django.contrib import admin
from .models import Entreprise

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom_entreprise', 'user_principal', 'palier', 'date_creation')
    search_fields = ('nom_entreprise', 'user_principal__username', 'user_principal__email')
    list_filter = ('palier', 'date_creation')
