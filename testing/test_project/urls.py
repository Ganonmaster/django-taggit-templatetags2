import os
from django.conf.urls import include, url


from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls), name='admin'),
]

if "DJANGO_SETTINGS_MODULE" in os.environ:
    from django.conf import settings
    from django.conf.urls.static import static
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
        show_indexes=True
    )
