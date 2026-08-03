"""
URL configuration for decore project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from .views import service_worker

urlpatterns = [
    path('admin/', admin.site.urls),
    path('service-worker.js', service_worker, name='service-worker'),

    path('', RedirectView.as_view(pattern_name='dashboard:index', permanent=False)),

    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('employees/', include('employees.urls')),
    path('worksites/', include('worksites.urls')),
    path('attendance/', include('attendance.urls')),
    path('salaries/', include('salaries.urls')),
    path('payments/', include('payments.urls')),
    path('materials/', include('materials.urls')),
    path('expenses/', include('expenses.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('settings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
