from django.urls import path
from . import views

app_name = "entreprises_app"

urlpatterns = [
    path('entreprise/admin/profil/<int:pk>/', views.EntrepriseProfilView.as_view(), name="entreprise-profil"),
]