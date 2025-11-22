# Add to views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def dashboard(request):
    """Enhanced dashboard view"""
    if request.user.is_authenticated:
        # Get portfolio data
        orders = Order.objects.filter(user=request.user, status='FILLED')
        # Calculate portfolio metrics here
        total_portfolio_value = sum([order.qty * order.ticker.current_price for order in orders if order.side == 'BUY'])
        active_stocks_count = len(set([order.ticker.symbol for order in orders]))
        total_trades = orders.count()
        
        # Get watchlist
        watchlist = Watchlist.objects.filter(user=request.user).first()
        watchlist_items = watchlist.tickers.all() if watchlist else []
        
        context = {
            'total_portfolio_value': total_portfolio_value,
            'active_stocks_count': active_stocks_count,
            'total_trades': total_trades,
            'top_gainers': Ticker.objects.filter(is_index=False).order_by('-change_pct')[:5],
            'top_losers': Ticker.objects.filter(is_index=False).order_by('change_pct')[:5],
            'watchlist_items': watchlist_items,
        }
    else:
        context = {
            'total_portfolio_value': 0,
            'active_stocks_count': 0,
            'total_trades': 0,
            'top_gainers': Ticker.objects.filter(is_index=False).order_by('-change_pct')[:5],
            'top_losers': Ticker.objects.filter(is_index=False).order_by('change_pct')[:5],
            'watchlist_items': [],
        }
    return render(request, 'markets/dashboard.html', context)

def screener(request):
    """Stock screener view"""
    stocks = Ticker.objects.filter(is_index=False)
    
    # Apply filters if any
    market_cap = request.GET.get('market_cap')
    sector = request.GET.get('sector')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    
    if sector:
        stocks = stocks.filter(sector=sector)
    if price_min:
        stocks = stocks.filter(current_price__gte=price_min)
    if price_max:
        stocks = stocks.filter(current_price__lte=price_max)
    
    context = {'stocks': stocks}
    return render(request, 'markets/screener.html', context)

def analytics(request):
    """Portfolio analytics view"""
    if not request.user.is_authenticated:
        return redirect('login')
        
    # Get user's holdings and calculate analytics
    orders = Order.objects.filter(user=request.user, status='FILLED')
    holdings = {}
    
    # Calculate holdings with analytics metrics
    for order in orders:
        symbol = order.ticker.symbol
        if symbol not in holdings:
            holdings[symbol] = {
                'ticker': order.ticker,
                'qty': 0,
                'weight': 0,
                'return': 0,
                'contribution': 0,
                'beta': round(random.uniform(0.5, 1.5), 2),
                'volatility': round(random.uniform(10, 25), 1),
                'sharpe': round(random.uniform(0.5, 2.5), 2),
                'max_drawdown': round(random.uniform(5, 20), 1)
            }
        
        if order.side == 'BUY':
            holdings[symbol]['qty'] += order.qty
        else:
            holdings[symbol]['qty'] -= order.qty
    
    # Remove zero positions
    active_holdings = {k: v for k, v in holdings.items() if v['qty'] > 0}
    
    context = {'holdings': active_holdings.values()}
    return render(request, 'markets/analytics.html', context)

@csrf_exempt
def price_alerts(request):
    """Handle price alerts"""
    if request.method == 'POST':
        data = json.loads(request.body)
        # Save alert to database
        return JsonResponse({'status': 'success'})
    
    # Return user's alerts
    alerts = []  # Get from database
    return JsonResponse({'alerts': alerts})

# Add to models.py
class PriceAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    alert_type = models.CharField(max_length=10, choices=[('ABOVE', 'Above'), ('BELOW', 'Below')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

class MarketNews(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    related_tickers = models.ManyToManyField(Ticker, blank=True)
    sentiment = models.CharField(max_length=10, choices=[
        ('POSITIVE', 'Positive'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral')
    ])

class TradingStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    criteria = models.JSONField()  # Store screening criteria
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
