from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

V1 = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),

    path(V1 + 'auth/',         include('apps.users.urls',        namespace='auth')),
    path(V1 + 'wallets/',      include('apps.wallets.urls',      namespace='wallets')),
    path(V1 + 'transactions/', include('apps.transactions.urls', namespace='transactions')),
    path(V1 + 'comptes/',      include('apps.comptes.urls',      namespace='comptes')),
    path(V1 + 'abonnements/',  include('apps.abonnements.urls',  namespace='abonnements')),
    path(V1 + 'users/',  include('apps.users.urls',  namespace='users')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
