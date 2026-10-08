from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from django.http import FileResponse


def home(request):
    return FileResponse(
        open(settings.BASE_DIR / 'index.html', 'rb'),
        content_type='text/html'
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reconciliation.urls')),

    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),

    path(
        'swagger/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    path('', home),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)