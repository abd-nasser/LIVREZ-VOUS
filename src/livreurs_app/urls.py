from django.urls import path


from . import views

app_name = 'livreurs_app'

urlpatterns = [
    path('livreurs/', views.ListLivreursView.as_view(), name='list-livreurs'),
    path('livreur/<int:pk>/profil/', views.LivreurProfileView.as_view(), name='livreur-profil'),
    path('livreur/<int:pk>/disponibilite/', views.disponibilite_livreur, name='livreur-disponibilite'),
]