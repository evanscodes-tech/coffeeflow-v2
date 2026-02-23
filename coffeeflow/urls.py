from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as accounts_views  # Changed import

# Admin site customization
admin.site.site_header = '☕ CoffeeFlow Administration'
admin.site.site_title = 'CoffeeFlow Admin'
admin.site.index_title = 'Coffee Collection System Dashboard'
admin.site.site_url = '/'

urlpatterns = [
    path('', accounts_views.home, name='home'),  # Updated to use accounts_views
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),  # Make sure this matches
    path('farmers/', include('apps.farmers.urls')),
    path('deliveries/', include('apps.deliveries.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api/', include('apps.mobile_api.urls')),
    path('reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)