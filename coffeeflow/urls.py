from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from apps.accounts import views as accounts_views

# Admin site customization
admin.site.site_header = '☕ CoffeeFlow Administration'
admin.site.site_title = 'CoffeeFlow Admin'
admin.site.index_title = 'Coffee Collection System Dashboard'
admin.site.site_url = '/'


@staff_member_required
def clear_recent_actions(request):
    """Clear recent actions for the current user"""
    if request.method == 'POST':
        LogEntry.objects.filter(user=request.user).delete()
    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


urlpatterns = [
    path('', accounts_views.home, name='home'),
     path('admin/clear-recent-actions/', clear_recent_actions, name='clear_recent_actions'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('farmers/', include('apps.farmers.urls')),
    path('deliveries/', include('apps.deliveries.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api/', include('apps.mobile_api.urls')),
    path('reports/', include('apps.reports.urls')),
    path('staff/', include('apps.staff_portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)