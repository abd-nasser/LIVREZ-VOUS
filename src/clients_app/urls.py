from django.urls import path
from . import views

app_name = 'clients_app'

urlpatterns = [
    path('clients/<int:pk>/', views.ClientProfileView.as_view(), name='client-profil'),
]