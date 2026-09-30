from django.urls import path
from . import views

app_name = "accounts_app"

urlpatterns = [
    path('inscription/livreurs/', views.CreateLivreurView.as_view(), name="inscription-livreurs")
]
