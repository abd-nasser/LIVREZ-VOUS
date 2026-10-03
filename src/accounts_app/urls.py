from django.urls import path
from . import views

app_name = "accounts_app"

urlpatterns = [
    path('connexion/', views.login_view, name="login"),
    path('deconnexion/', views.logout_view, name="logout"),
    path('inscription/livreurs/', views.CreateLivreurView.as_view(), name="inscription-livreurs"),
    path('inscription/clients/', views.CreateClientView.as_view(), name="inscription-clients"),
]
