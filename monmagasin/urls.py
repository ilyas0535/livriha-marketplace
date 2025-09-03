from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from django.conf.urls.i18n import i18n_patterns
from . import views
from seo_views import robots_txt, sitemap_xml

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('en/', views.home, name='home_en'),
    path('fr/', views.home, name='home_fr'), 
    path('ar/', views.home, name='home_ar'),
    path('accounts/', include('accounts.urls')),
    path('shop/', include('shops.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    # SEO URLs
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)