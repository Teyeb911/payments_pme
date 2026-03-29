from django.urls import path
from .views import CompteListCreateView, CompteDetailView, PaiementsEntrantsView

app_name = 'comptes'

urlpatterns = [
    path('',                         CompteListCreateView.as_view(),  name='liste'),
    path('<int:pk>/',                CompteDetailView.as_view(),      name='detail'),
    path('<int:pk>/paiements/',      PaiementsEntrantsView.as_view(), name='paiements'),
]
