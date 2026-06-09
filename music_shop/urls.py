from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic import TemplateView

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_xml(request):
    base = f"{request.scheme}://{request.get_host()}"
    paths = ["", "catalog/", "track_catalog/", "ambient/", "merchandise/", "about/", "privacy/", "terms/"]
    urls = "\n".join(
        f"  <url><loc>{base}/{path}</loc><changefreq>weekly</changefreq></url>"
        for path in paths
    )
    body = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>'
    return HttpResponse(body, content_type="application/xml")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('', include('shop.urls')), # Include all the URLs from 'shop' app
]
