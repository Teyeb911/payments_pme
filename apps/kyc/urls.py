from django.urls import path

from .views import KycAnalyzeView, KycCompleteView, KycStatusView

app_name = 'kyc'

urlpatterns = [
    path('analyze/',            KycAnalyzeView.as_view(),  name='analyze'),
    path('complete/',           KycCompleteView.as_view(), name='complete'),
    path('status/<int:user_id>/', KycStatusView.as_view(), name='status'),
]
