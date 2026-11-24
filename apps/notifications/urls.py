from django.urls import path

from .views import DeviceTokenView

app_name = 'notifications'

urlpatterns = [
    path('device-token/', DeviceTokenView.as_view(), name='device-token'),
]
