from django.urls import path

from .views import KycAnalyzeView, KycCompleteView, KycStatusView, KycValiderView
from .nova_views import NovaStatusView, NovaVerifyView

app_name = 'kyc'

urlpatterns = [
    path('analyze/',                    KycAnalyzeView.as_view(),   name='analyze'),
    path('complete/',                   KycCompleteView.as_view(),  name='complete'),
    path('status/<int:user_id>/',       KycStatusView.as_view(),    name='status'),
    path('valider/<int:user_id>/',      KycValiderView.as_view(),   name='valider'),
    # NovaKYC (document + visage + vivacité + risque + décision)
    path('nova/status/',                NovaStatusView.as_view(),   name='nova-status'),
    path('nova/verify/',                NovaVerifyView.as_view(),   name='nova-verify'),
]
