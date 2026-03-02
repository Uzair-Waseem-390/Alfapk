from django.http import HttpResponse
from django.contrib import admin
from django.urls import path


def root(request):
    return HttpResponse("hello from awaab")



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root, name='root'),
]
