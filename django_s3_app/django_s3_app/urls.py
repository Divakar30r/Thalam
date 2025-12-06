from django.urls import path, include
from django.conf import settings

urlpatterns = [
    # Admin interface removed - using Keycloak for authentication
    # path('admin/', admin.site.urls),
    path(settings.API_PREFIX, include('attachments.urls')),
]