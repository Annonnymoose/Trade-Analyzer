from django.contrib import admin
from .models import Ticker, PriceBar, Watchlist, Order

@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'sector', 'price', 'change_pct', 'is_index')
    list_filter = ('sector', 'exchange', 'is_index')
    search_fields = ('symbol', 'name')

@admin.register(PriceBar)
class PriceBarAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'date', 'open', 'high', 'low', 'close', 'volume')
    list_filter = ('ticker', 'date')
    date_hierarchy = 'date'

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'ticker', 'added_at')
    list_filter = ('added_at', 'ticker')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'ticker', 'order_type', 'quantity', 'price', 'status', 'created_at')
    list_filter = ('status', 'order_type', 'ticker')
    date_hierarchy = 'created_at'
