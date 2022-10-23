from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('product.urls')),
    path('api/', include('api.urls')),
    path('support/', include('support.urls')),
    path('admin/', admin.site.urls),
]
