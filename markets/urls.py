from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('stocks/', views.stocks, name='stocks'),
    path('stocks/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/<int:item_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('place-order/', views.place_order, name='place_order'),
    path('api/stocks/<str:symbol>/data/', views.get_stock_data, name='stock_data'),
    
    # Enhanced features
    path('dashboard/', views.dashboard, name='dashboard'),
    path('screener/', views.screener, name='screener'),
    path('analytics/', views.analytics, name='analytics'),
    path('advanced-trading/', views.advanced_trading, name='advanced_trading'),
    path('trade-history/', views.trade_history, name='trade_history'),
    
    # API endpoints
    path('api/chart-data/<str:symbol>/', views.get_chart_data, name='chart_data'),
    path('api/orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('api/orders/cancel-all/', views.cancel_all_orders, name='cancel_all_orders'),
    path('api/search-stocks/', views.search_stocks, name='search_stocks'),
    
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
]
