from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        "status": "healthy",
        "service": "BudgetFlow Backend API",
        "version": "1.0.0"
    })

urlpatterns = [
    path('', health_check, name='root-health'),
    path('api/health/', health_check, name='api-health'),
    path('django-admin/', admin.site.urls),
    path('api/auth/', include('custom_auth.urls')),
    path('api/', include('finance.urls')),
    path('api/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
