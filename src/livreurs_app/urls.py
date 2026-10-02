from django.urls import path

from .views import LivreurProfileView

app_name = 'livreurs_app'

urlpatterns = [
    path('<int:pk>/profil/', LivreurProfileView.as_view(), name='profil'),
]