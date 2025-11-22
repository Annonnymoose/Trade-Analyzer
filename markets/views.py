from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum, F, Count, Case, When, DecimalField
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from decimal import Decimal
import json
from datetime import datetime, timedelta
from .models import Ticker, PriceBar, Watchlist, Order
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def home(request):
    # Get indices
    indices = Ticker.objects.filter(is_index=True).order_by('symbol')
    
    # Get top movers (excluding indices)
    top_movers = Ticker.objects.filter(is_index=False).order_by('-change_pct')[:6]
    
    context = {
        'indices': indices,
        'top_movers': top_movers,
    }
    return render(request, 'markets/home_modern.html', context)

def stocks(request):
    query = request.GET.get('q', '')
    sector = request.GET.get('sector', '')
    
    stocks = Ticker.objects.filter(is_index=False)
    
    if query:
        stocks = stocks.filter(
            Q(symbol__icontains=query) | 
            Q(name__icontains=query)
        )
    
    if sector:
        stocks = stocks.filter(sector=sector)
    
    sectors = Ticker.objects.values_list('sector', flat=True).distinct()
    
    context = {
        'stocks': stocks,
        'sectors': sectors,
        'current_sector': sector,
        'query': query,
    }
    return render(request, 'markets/stocks_modern.html', context)

def stock_detail(request, symbol):
    stock = get_object_or_404(Ticker, symbol=symbol)
    
    # Get historical data for charts
    historical_data = PriceBar.objects.filter(ticker=stock).order_by('-date')[:180]
    
    # Get related stocks from same sector
    related_stocks = Ticker.objects.filter(
        sector=stock.sector
    ).exclude(id=stock.id)[:5]
    
    # Check if user has this stock in watchlist
    in_watchlist = False
    if request.user.is_authenticated:
        in_watchlist = Watchlist.objects.filter(user=request.user, ticker=stock).exists()
    
    context = {
        'stock': stock,
        'historical_data': historical_data,
        'related_stocks': related_stocks,
        'in_watchlist': in_watchlist,
    }
    return render(request, 'markets/stock_detail.html', context)

@login_required
def watchlist(request):
    # Get user's watchlist items
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('ticker')
    
    # Calculate stats
    gainers_count = watchlist_items.filter(ticker__change_pct__gt=0).count()
    losers_count = watchlist_items.filter(ticker__change_pct__lt=0).count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        ticker_id = request.POST.get('ticker_id')
        ticker = get_object_or_404(Ticker, id=ticker_id)
        
        if action == 'add':
            watchlist_item, created = Watchlist.objects.get_or_create(
                user=request.user,
                ticker=ticker
            )
            if created:
                messages.success(request, f'{ticker.symbol} added to watchlist')
            else:
                messages.info(request, f'{ticker.symbol} is already in your watchlist')
        elif action == 'remove':
            Watchlist.objects.filter(user=request.user, ticker=ticker).delete()
            messages.success(request, f'{ticker.symbol} removed from watchlist')
    
    context = {
        'watchlist_items': watchlist_items,
        'gainers_count': gainers_count,
        'losers_count': losers_count,
    }
    return render(request, 'watchlist_modern.html', context)

@login_required
def portfolio(request):
    # Get user's filled orders
    orders = Order.objects.filter(
        user=request.user,
        status='FILLED'
    ).order_by('-created_at')
    
    # Calculate holdings and performance metrics
    holdings = {}
    total_investment = Decimal('0')
    total_current_value = Decimal('0')
    realized_pnl = Decimal('0')
    
    for order in orders:
        symbol = order.ticker.symbol
        if symbol not in holdings:
            holdings[symbol] = {
                'symbol': symbol,
                'company_name': order.ticker.name,
                'ticker': order.ticker,
                'shares': 0,
                'avg_cost': Decimal('0'),
                'total_cost': Decimal('0'),
                'current_price': Decimal(str(order.ticker.price)),
                'realized_pnl': Decimal('0'),
                'trades': 0
            }
        
        h = holdings[symbol]
        price = Decimal(str(order.price))
        
        if order.order_type == 'BUY':
            # Update position for BUY
            old_total = h['shares'] * h['avg_cost']
            new_total = price * order.quantity
            h['shares'] += order.quantity
            h['total_cost'] = old_total + new_total
            h['avg_cost'] = h['total_cost'] / h['shares'] if h['shares'] > 0 else Decimal('0')
        else:
            # Update position and calculate realized P&L for SELL
            sell_value = price * order.quantity
            cost_basis = h['avg_cost'] * order.quantity
            h['realized_pnl'] += sell_value - cost_basis
            realized_pnl += sell_value - cost_basis
            
            h['shares'] -= order.quantity
            if h['shares'] > 0:
                h['total_cost'] = h['avg_cost'] * h['shares']
        
        h['trades'] += 1
        
        # Calculate current value and unrealized P&L
        if h['shares'] > 0:
            h['current_price'] = Decimal(str(order.ticker.price))
            h['market_value'] = h['shares'] * h['current_price']
            h['unrealized_pnl'] = h['market_value'] - h['total_cost']
            h['return_pct'] = (
                (h['market_value'] / h['total_cost'] - 1) * 100
                if h['total_cost'] > 0 else Decimal('0')
            )
            h['day_change'] = h['shares'] * Decimal(str(order.ticker.change))
            h['day_change_pct'] = Decimal(str(order.ticker.change_pct))
    
    # Remove closed positions
    active_holdings = [v for v in holdings.values() if v['shares'] > 0]
    
    # Calculate portfolio totals
    for h in active_holdings:
        total_investment += h['total_cost']
        total_current_value += h['market_value']
    
    total_gain_loss = total_current_value - total_investment
    total_return_pct = (
        (total_current_value / total_investment - 1) * 100
        if total_investment > 0 else Decimal('0')
    )
    
    # Calculate day change
    day_change = sum(h['day_change'] for h in active_holdings)
    
    # Get top positions for allocation chart
    top_positions = sorted(active_holdings, key=lambda x: x['market_value'], reverse=True)[:5]
    
    context = {
        'holdings': active_holdings,
        'recent_orders': orders[:10],
        'total_value': total_current_value,
        'total_gain_loss': total_gain_loss,
        'total_return_pct': total_return_pct,
        'day_change': day_change,
        'top_positions': top_positions,
    }
    return render(request, 'portfolio_modern.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            ticker_id = request.POST.get('ticker_id')
            side = request.POST.get('side')
            qty = int(request.POST.get('qty'))
            
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            
            ticker = get_object_or_404(Ticker, id=ticker_id)
            
            # Get user's current position in this stock
            orders = Order.objects.filter(
                user=request.user,
                ticker=ticker,
                status='FILLED'
            )
            
            position_qty = 0
            position_value = 0
            
            for order in orders:
                if order.side == 'BUY':
                    position_qty += order.qty
                    position_value += order.qty * float(order.price)
                else:
                    position_qty -= order.qty
                    position_value -= order.qty * float(order.price)
            
            # Validate SELL orders against current position
            if side == 'SELL' and qty > position_qty:
                messages.error(request, f'Cannot sell {qty} shares. Current position: {position_qty}')
                return redirect('stock_detail', symbol=ticker.symbol)
            
            # Calculate average price for position tracking
            avg_price = position_value / position_qty if position_qty > 0 else 0
            
            # Create and save the order
            order = Order.objects.create(
                user=request.user,
                ticker=ticker,
                side=side,
                qty=qty,
                price=ticker.current_price,
                status='FILLED'
            )
            
            # Update position calculations
            if side == 'BUY':
                new_qty = position_qty + qty
                new_value = position_value + (qty * float(ticker.current_price))
                avg_price = new_value / new_qty
                msg = f'Bought {qty} shares of {ticker.symbol} at ₹{ticker.current_price}'
            else:
                pnl = (float(ticker.current_price) - avg_price) * qty
                msg = f'Sold {qty} shares of {ticker.symbol} at ₹{ticker.current_price} (P&L: ₹{pnl:,.2f})'
            
            messages.success(request, msg)
            return redirect('stock_detail', symbol=ticker.symbol)
            
        except (ValueError, TypeError) as e:
            messages.error(request, str(e))
            return redirect('stock_detail', symbol=ticker.symbol)
    
    return redirect('home')

def get_stock_data(request, symbol):
    """API endpoint for chart data"""
    stock = get_object_or_404(Ticker, symbol=symbol)
    period = request.GET.get('period', '1m')  # Default to 1 month
    
    # Define the number of days based on period
    days = {
        '7d': 7,
        '1m': 30,
        '3m': 90,
        '6m': 180,
    }.get(period, 30)
    
    data = PriceBar.objects.filter(
        ticker=stock
    ).order_by('-date')[:days]
    
    chart_data = [{
        't': bar.date.isoformat(),
        'o': float(bar.open),
        'h': float(bar.high),
        'l': float(bar.low),
        'c': float(bar.close),
        'v': bar.volume
    } for bar in data]
    
    return JsonResponse({'data': chart_data})

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Stock Market Analyzer.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register_modern.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'registration/login_modern.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# Enhanced Features Views

@login_required
def dashboard(request):
    """Enhanced dashboard with live market data and portfolio overview"""
    # Get user's portfolio summary
    user_orders = Order.objects.filter(user=request.user).select_related('ticker')
    
    # Calculate portfolio positions
    positions = {}
    for order in user_orders:
        symbol = order.ticker.symbol
        if symbol not in positions:
            positions[symbol] = {
                'symbol': symbol,
                'ticker': order.ticker,
                'shares': 0,
                'total_cost': Decimal('0.00'),
                'trades': []
            }
        
        if order.side == 'buy':
            positions[symbol]['shares'] += order.quantity
            positions[symbol]['total_cost'] += order.quantity * order.price
        else:
            positions[symbol]['shares'] -= order.quantity
            positions[symbol]['total_cost'] -= order.quantity * order.price
        
        positions[symbol]['trades'].append(order)
    
    # Calculate current values
    portfolio_data = []
    total_value = Decimal('0.00')
    total_cost = Decimal('0.00')
    
    for pos_data in positions.values():
        if pos_data['shares'] > 0:
            current_price = pos_data['ticker'].price
            market_value = pos_data['shares'] * current_price
            avg_cost = pos_data['total_cost'] / pos_data['shares'] if pos_data['shares'] > 0 else Decimal('0.00')
            gain_loss = market_value - (pos_data['shares'] * avg_cost)
            gain_loss_pct = (gain_loss / (pos_data['shares'] * avg_cost)) * 100 if avg_cost > 0 else 0
            
            portfolio_data.append({
                'symbol': pos_data['symbol'],
                'ticker': pos_data['ticker'],
                'shares': pos_data['shares'],
                'avg_cost': avg_cost,
                'current_price': current_price,
                'market_value': market_value,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct,
            })
            
            total_value += market_value
            total_cost += pos_data['shares'] * avg_cost
    
    # Market overview
    indices = Ticker.objects.filter(is_index=True)
    top_gainers = Ticker.objects.filter(is_index=False).order_by('-change_pct')[:5]
    top_losers = Ticker.objects.filter(is_index=False).order_by('change_pct')[:5]
    
    # Recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Watchlist
    watchlist = Watchlist.objects.filter(user=request.user).select_related('ticker')
    
    context = {
        'portfolio_data': portfolio_data,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_value - total_cost,
        'total_gain_loss_pct': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        'indices': indices,
        'top_gainers': top_gainers,
        'top_losers': top_losers,
        'recent_orders': recent_orders,
        'watchlist': watchlist,
    }
    
    return render(request, 'markets/dashboard.html', context)

@login_required
def screener(request):
    """Stock screener with advanced filtering"""
    # Get filter parameters
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_volume = request.GET.get('min_volume', '')
    max_volume = request.GET.get('max_volume', '')
    min_change = request.GET.get('min_change', '')
    max_change = request.GET.get('max_change', '')
    sector = request.GET.get('sector', '')
    market_cap = request.GET.get('market_cap', '')
    
    # Start with all non-index stocks
    stocks = Ticker.objects.filter(is_index=False)
    
    # Apply filters
    if min_price:
        stocks = stocks.filter(price__gte=min_price)
    if max_price:
        stocks = stocks.filter(price__lte=max_price)
    if min_volume:
        stocks = stocks.filter(volume__gte=min_volume)
    if max_volume:
        stocks = stocks.filter(volume__lte=max_volume)
    if min_change:
        stocks = stocks.filter(change_pct__gte=min_change)
    if max_change:
        stocks = stocks.filter(change_pct__lte=max_change)
    if sector:
        stocks = stocks.filter(sector=sector)
    if market_cap:
        # Simple market cap filtering (this would need actual market cap data)
        if market_cap == 'large':
            stocks = stocks.filter(price__gte=100)
        elif market_cap == 'mid':
            stocks = stocks.filter(price__gte=50, price__lt=100)
        elif market_cap == 'small':
            stocks = stocks.filter(price__lt=50)
    
    # Order by relevance
    stocks = stocks.order_by('-change_pct')
    
    # Get available sectors
    sectors = Ticker.objects.values_list('sector', flat=True).distinct()
    
    context = {
        'stocks': stocks,
        'sectors': sectors,
        'filters': {
            'min_price': min_price,
            'max_price': max_price,
            'min_volume': min_volume,
            'max_volume': max_volume,
            'min_change': min_change,
            'max_change': max_change,
            'sector': sector,
            'market_cap': market_cap,
        }
    }
    
    return render(request, 'markets/screener.html', context)

@login_required
def analytics(request):
    """Portfolio analytics and performance metrics"""
    # Get user's orders
    user_orders = Order.objects.filter(user=request.user).select_related('ticker').order_by('created_at')
    
    if not user_orders:
        return render(request, 'markets/analytics.html', {'no_data': True})
    
    # Calculate portfolio performance over time
    portfolio_history = []
    cumulative_cost = Decimal('0.00')
    positions = {}
    
    for order in user_orders:
        symbol = order.ticker.symbol
        
        if symbol not in positions:
            positions[symbol] = {'shares': 0, 'cost_basis': Decimal('0.00')}
        
        if order.side == 'buy':
            positions[symbol]['shares'] += order.quantity
            positions[symbol]['cost_basis'] += order.quantity * order.price
            cumulative_cost += order.quantity * order.price
        else:
            positions[symbol]['shares'] -= order.quantity
            positions[symbol]['cost_basis'] -= order.quantity * order.price
            cumulative_cost -= order.quantity * order.price
        
        # Calculate current portfolio value
        current_value = Decimal('0.00')
        for pos_symbol, pos_data in positions.items():
            if pos_data['shares'] > 0:
                ticker = Ticker.objects.get(symbol=pos_symbol)
                current_value += pos_data['shares'] * ticker.price
        
        portfolio_history.append({
            'date': order.created_at.strftime('%Y-%m-%d'),
            'value': float(current_value),
            'cost': float(cumulative_cost),
            'gain_loss': float(current_value - cumulative_cost)
        })
    
    # Calculate sector allocation
    sector_allocation = {}
    total_portfolio_value = Decimal('0.00')
    
    for symbol, pos_data in positions.items():
        if pos_data['shares'] > 0:
            ticker = Ticker.objects.get(symbol=symbol)
            value = pos_data['shares'] * ticker.price
            total_portfolio_value += value
            
            sector = ticker.sector or 'Unknown'
            if sector not in sector_allocation:
                sector_allocation[sector] = Decimal('0.00')
            sector_allocation[sector] += value
    
    # Convert to percentages
    sector_percentages = {}
    if total_portfolio_value > 0:
        for sector, value in sector_allocation.items():
            sector_percentages[sector] = float((value / total_portfolio_value) * 100)
    
    # Trading statistics
    total_trades = user_orders.count()
    buy_orders = user_orders.filter(side='buy').count()
    sell_orders = user_orders.filter(side='sell').count()
    
    # Performance metrics
    if portfolio_history:
        latest = portfolio_history[-1]
        total_return = latest['gain_loss']
        total_return_pct = (total_return / latest['cost'] * 100) if latest['cost'] > 0 else 0
    else:
        total_return = 0
        total_return_pct = 0
    
    context = {
        'portfolio_history': json.dumps(portfolio_history),
        'sector_allocation': json.dumps(sector_percentages),
        'trading_stats': {
            'total_trades': total_trades,
            'buy_orders': buy_orders,
            'sell_orders': sell_orders,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'portfolio_value': float(total_portfolio_value),
        }
    }
    
    return render(request, 'markets/analytics.html', context)

@login_required
def advanced_trading(request):
    """Advanced trading interface"""
    # Get user's current positions
    user_orders = Order.objects.filter(user=request.user).select_related('ticker')
    
    positions = {}
    for order in user_orders:
        symbol = order.ticker.symbol
        if symbol not in positions:
            positions[symbol] = {
                'symbol': symbol,
                'company_name': order.ticker.name,
                'shares': 0,
                'total_cost': Decimal('0.00'),
            }
        
        if order.side == 'buy':
            positions[symbol]['shares'] += order.quantity
            positions[symbol]['total_cost'] += order.quantity * order.price
        else:
            positions[symbol]['shares'] -= order.quantity
            positions[symbol]['total_cost'] -= order.quantity * order.price
    
    # Calculate current values for positions
    position_list = []
    for pos_data in positions.values():
        if pos_data['shares'] > 0:
            ticker = Ticker.objects.get(symbol=pos_data['symbol'])
            avg_cost = pos_data['total_cost'] / pos_data['shares']
            current_price = ticker.price
            market_value = pos_data['shares'] * current_price
            gain_loss = market_value - (pos_data['shares'] * avg_cost)
            gain_loss_pct = (gain_loss / (pos_data['shares'] * avg_cost)) * 100 if avg_cost > 0 else 0
            
            position_list.append({
                'symbol': pos_data['symbol'],
                'company_name': pos_data['company_name'],
                'shares': pos_data['shares'],
                'avg_cost': avg_cost,
                'current_price': current_price,
                'market_value': market_value,
                'gain_loss': gain_loss,
                'gain_loss_percent': gain_loss_pct,
            })
    
    # Get active orders (for demo, we'll show recent orders)
    active_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Add calculated total to each order
    orders_with_total = []
    for order in active_orders:
        orders_with_total.append({
            'id': order.id,
            'created_at': order.created_at,
            'ticker': order.ticker,
            'side': order.side,
            'quantity': order.quantity,
            'price': order.price,
            'total': order.quantity * order.price,
        })
    
    context = {
        'positions': position_list,
        'orders': orders_with_total,
    }
    
    return render(request, 'markets/advanced_trading.html', context)

# API Views for Enhanced Features

@login_required
def get_chart_data(request, symbol):
    """Get chart data for a specific symbol"""
    stock = get_object_or_404(Ticker, symbol=symbol)
    period = request.GET.get('period', '1m')
    
    # Define the number of days based on period
    days = {
        '1d': 1,
        '1w': 7,
        '1m': 30,
        '3m': 90,
        '1y': 365,
    }.get(period, 30)
    
    data = PriceBar.objects.filter(
        ticker=stock
    ).order_by('-date')[:days]
    
    chart_data = [{
        'time': bar.date.isoformat(),
        'open': float(bar.open),
        'high': float(bar.high),
        'low': float(bar.low),
        'close': float(bar.close),
        'volume': bar.volume
    } for bar in reversed(data)]
    
    return JsonResponse({'data': chart_data})

@login_required
def cancel_order(request, order_id):
    """Cancel a specific order"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            # In a real system, you would cancel the order here
            # For now, we'll just delete it from the database
            order.delete()
            return JsonResponse({'success': True, 'message': 'Order canceled successfully'})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def cancel_all_orders(request):
    """Cancel all active orders for the user"""
    if request.method == 'POST':
        canceled_count = Order.objects.filter(user=request.user).count()
        Order.objects.filter(user=request.user).delete()
        return JsonResponse({
            'success': True, 
            'message': f'{canceled_count} orders canceled successfully'
        })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def add_to_watchlist(request):
    """Add a stock to user's watchlist"""
    symbol = request.GET.get('symbol')
    if symbol:
        ticker = get_object_or_404(Ticker, symbol=symbol)
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            ticker=ticker
        )
        if created:
            messages.success(request, f'{ticker.symbol} added to watchlist')
        else:
            messages.info(request, f'{ticker.symbol} is already in your watchlist')
    return redirect('watchlist')

@login_required
def remove_from_watchlist(request, item_id):
    """Remove a stock from user's watchlist"""
    try:
        watchlist_item = Watchlist.objects.get(id=item_id, user=request.user)
        symbol = watchlist_item.ticker.symbol
        watchlist_item.delete()
        messages.success(request, f'{symbol} removed from watchlist')
    except Watchlist.DoesNotExist:
        messages.error(request, 'Watchlist item not found')
    return redirect('watchlist')

@login_required
def trade_history(request):
    """View complete trade history"""
    orders = Order.objects.filter(user=request.user).select_related('ticker').order_by('-created_at')
    
    # Filter by symbol if provided
    symbol = request.GET.get('symbol')
    if symbol:
        orders = orders.filter(ticker__symbol=symbol)
    
    context = {
        'orders': orders,
        'symbol_filter': symbol,
    }
    return render(request, 'markets/trade_history.html', context)

def search_stocks(request):
    """Search for stocks by symbol or name"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    stocks = Ticker.objects.filter(
        Q(symbol__icontains=query) | Q(name__icontains=query),
        is_index=False
    )[:10]
    
    results = [{
        'symbol': stock.symbol,
        'name': stock.name,
        'price': float(stock.price),
        'change_pct': float(stock.change_pct),
    } for stock in stocks]
    
    return JsonResponse({'results': results})
