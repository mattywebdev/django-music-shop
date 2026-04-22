from django.urls import path
from . import views, account_views, api_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('catalog/', views.catalog, name='catalog'),
    path('ambient/', views.ambient, name='ambient'),
    path('add_to_cart/<str:item_type>/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path("cart/update/", views.update_cart_all, name="update_cart_all"),
    path('checkout/', views.checkout_view, name='checkout'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('success/', views.success, name='success'),
    path('remove_from_cart/<str:item_type>/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('login/', views.loginPage, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutUser, name='logout'),
    path('merchandise/', views.merchandise_view, name='merchandise'),
    path('about/', views.about, name='about'),
    path('track_catalog/', views.track_catalog, name='track_catalog'),

    # Account
    path('account/', account_views.account_dashboard, name='account_dashboard'),
    path('account/orders/', account_views.order_list, name='order_list'),
    path('account/orders/<int:order_id>/', account_views.order_detail, name='order_detail'),
    path('account/favorites/', account_views.favorites, name='favorites'),
    path('favorite/toggle/<str:item_type>/<int:item_id>/', account_views.toggle_favorite, name='toggle_favorite'),
    path('account/orders/', account_views.order_list, name='account_orders'),
    path('account/orders/<int:order_id>/', account_views.order_detail, name='account_order_detail'),

    # APIs (single source of truth)
    path('api/albums/', api_views.albums_api, name='albums_api'),
    path('api/tracks/', api_views.tracks_api, name='tracks_api'),
    path('api/search_suggest/', api_views.search_suggest, name='search_suggest'),
    path('api/ping/', views.api_ping, name='api_ping'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)