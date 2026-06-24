from django.urls import path

from . import views


urlpatterns = [
    path("api/payments/create/", views.CreatePaymentView.as_view()),
    path("api/payments/<uuid:payment_id>/status/", views.PaymentStatusView.as_view()),
    path("api/partner/dashboard/", views.PartnerDashboardView.as_view()),
    path("api/partner/credentials/", views.PartnerCredentialsView.as_view()),
    path("api/partner/plans/", views.PartnerPlansView.as_view()),
    path("api/partner/plans/<uuid:plan_id>/", views.PartnerPlanDetailView.as_view()),
    path("api/partner/payments/", views.PartnerPaymentsView.as_view()),
    path("pay/<uuid:payment_id>/", views.PaymentPageView.as_view()),
    path("pay/<uuid:payment_id>/send-otp/", views.SendOTPView.as_view()),
    path("pay/<uuid:payment_id>/confirm/", views.ConfirmPaymentView.as_view()),
]
