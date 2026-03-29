from django.urls import path
from .views import (
    PlanListView,
    MonAbonnementView,
    SouscrireView,
    ResilierView,
    RenouvelerView,
    AllAbonnementsView,
)

app_name = 'abonnements'

urlpatterns = [
    # Plans
    path('plans/',      PlanListView.as_view(),      name='plans'),

    # Commerçant
    path('me/',         MonAbonnementView.as_view(),  name='mon-abonnement'),
    path('souscrire/',  SouscrireView.as_view(),      name='souscrire'),
    path('resilier/',   ResilierView.as_view(),       name='resilier'),
    path('renouveler/', RenouvelerView.as_view(),     name='renouveler'),

    # Admin
    path('all/',        AllAbonnementsView.as_view(), name='all'),
]
