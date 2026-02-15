from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views

# Admin site customization (moved here from settings.py)
admin.site.site_header = '☕ CoffeeFlow Administration'
admin.site.site_title = 'CoffeeFlow Admin'
admin.site.index_title = 'Coffee Collection System Dashboard'
admin.site.site_url = '/'

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('farmers/', include('farmers.urls')),
    path('deliveries/', include('deliveries.urls')),
    path('payments/', include('payments.urls')),
    path('api/', include('mobile_api.urls')),
     path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)