from django.http import HttpResponse
from django.contrib import admin
from django.urls import path, include
from django.template import loader
from django.conf import settings
from django.conf.urls.static import static

def root(request):
    template = loader.get_template('root.html')
    return HttpResponse(template.render())

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root, name='root'),
    path('accounts/', include('accounts.urls')),
]

# Add this to serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)