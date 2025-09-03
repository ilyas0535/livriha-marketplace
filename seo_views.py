from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from shops.models import Shop
from products.models import Product

def robots_txt(request):
    template = loader.get_template('robots.txt')
    return HttpResponse(template.render(), content_type='text/plain')

def sitemap_xml(request):
    """Generate XML sitemap for SEO"""
    urls = []
    
    # Static pages
    static_pages = [
        {'loc': request.build_absolute_uri('/'), 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': request.build_absolute_uri('/accounts/register/'), 'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': request.build_absolute_uri('/accounts/login/'), 'priority': '0.6', 'changefreq': 'monthly'},
    ]
    urls.extend(static_pages)
    
    # Shop pages
    for shop in Shop.objects.all():
        urls.append({
            'loc': request.build_absolute_uri(f'/shop/{shop.slug}/'),
            'priority': '0.8',
            'changefreq': 'weekly'
        })
    
    # Product pages
    for product in Product.objects.all()[:1000]:  # Limit to 1000 products
        urls.append({
            'loc': request.build_absolute_uri(f'/product/{product.id}/'),
            'priority': '0.7',
            'changefreq': 'weekly'
        })
    
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
    
    for url in urls:
        xml_content += f'''
    <url>
        <loc>{url['loc']}</loc>
        <priority>{url['priority']}</priority>
        <changefreq>{url['changefreq']}</changefreq>
    </url>'''
    
    xml_content += '''
</urlset>'''
    
    return HttpResponse(xml_content, content_type='application/xml')