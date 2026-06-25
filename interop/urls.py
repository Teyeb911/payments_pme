from django.urls import path
from . import views

urlpatterns = [
    path("api/interop/verify-user/", views.VerifyUserView.as_view()),
    path("api/interop/receive/", views.ReceiveTransferView.as_view()),
]
