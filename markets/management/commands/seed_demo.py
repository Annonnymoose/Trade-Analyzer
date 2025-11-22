import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from markets.models import Ticker, PriceBar, Watchlist, Order

class Command(BaseCommand):
    help = 'Seeds the database with sample stock market data'

    def handle(self, *args, **options):
        # Create demo user
        user, _ = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'is_active': True
            }
        )
        user.set_password('demo123')
        user.save()

        self.stdout.write('Created demo user')

        # Seed example tickers
        tickers_data = [
            # Indices
            ('NIFTY50', 'NIFTY 50 Index', 'NSE', 'Index', True),
            ('SENSEX', 'S&P BSE SENSEX', 'BSE', 'Index', True),
            # Stocks
            ('RELIANCE', 'Reliance Industries Ltd.', 'NSE', 'Oil & Gas', False),
            ('TCS', 'Tata Consultancy Services Ltd.', 'NSE', 'IT', False),
            ('INFY', 'Infosys Ltd.', 'NSE', 'IT', False),
            ('HDFCBANK', 'HDFC Bank Ltd.', 'NSE', 'Banking', False),
            ('ICICIBANK', 'ICICI Bank Ltd.', 'NSE', 'Banking', False),
            ('ITC', 'ITC Ltd.', 'NSE', 'FMCG', False),
            ('SBIN', 'State Bank of India', 'NSE', 'Banking', False),
            ('LT', 'Larsen & Toubro Ltd.', 'NSE', 'Construction', False),
            ('HINDUNILVR', 'Hindustan Unilever Ltd.', 'NSE', 'FMCG', False),
            ('ASIANPAINT', 'Asian Paints Ltd.', 'NSE', 'Paints', False),
            ('KOTAKBANK', 'Kotak Mahindra Bank Ltd.', 'NSE', 'Banking', False),
            ('AXISBANK', 'Axis Bank Ltd.', 'NSE', 'Banking', False),
        ]

        tickers = []
        for symbol, name, exchange, sector, is_index in tickers_data:
            price = random.uniform(100, 5000)
            change = random.uniform(-5, 5)
            ticker = Ticker.objects.create(
                symbol=symbol,
                name=name,
                exchange=exchange,
                sector=sector,
                current_price=Decimal(str(round(price, 2))),
                change_pct=Decimal(str(round(change, 2))),
                is_index=is_index
            )
            tickers.append(ticker)
            self.stdout.write(f'Created ticker {symbol}')

        # Generate historical data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)
        
        for ticker in tickers[:7]:  # Generate data for first 7 tickers only
            current_date = start_date
            last_close = float(ticker.current_price)
            
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Only trading days
                    # Generate OHLCV data with some randomness but trending
                    change = random.uniform(-2, 2)
                    price_volatility = last_close * 0.02
                    
                    open_price = last_close * (1 + random.uniform(-0.01, 0.01))
                    close_price = open_price * (1 + change/100)
                    high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
                    low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
                    volume = int(random.uniform(100000, 1000000))
                    
                    PriceBar.objects.create(
                        ticker=ticker,
                        date=current_date,
                        open=Decimal(str(round(open_price, 2))),
                        high=Decimal(str(round(high_price, 2))),
                        low=Decimal(str(round(low_price, 2))),
                        close=Decimal(str(round(close_price, 2))),
                        volume=volume
                    )
                    
                    last_close = close_price
                current_date += timedelta(days=1)
            
            self.stdout.write(f'Generated historical data for {ticker.symbol}')

        # Create demo watchlist
        watchlist = Watchlist.objects.create(
            user=user,
            name='Starter Watchlist'
        )
        watchlist.tickers.add(*tickers[2:8])  # Add some non-index stocks
        self.stdout.write('Created demo watchlist')

        # Create some demo orders
        for ticker in tickers[2:5]:  # Create orders for first 3 stocks
            # Buy order
            qty = random.randint(10, 100)
            Order.objects.create(
                user=user,
                ticker=ticker,
                side='BUY',
                qty=qty,
                price=ticker.current_price,
                status='FILLED'
            )
            
            # Sell part of position
            if random.random() > 0.5:
                sell_qty = random.randint(1, qty)
                Order.objects.create(
                    user=user,
                    ticker=ticker,
                    side='SELL',
                    qty=sell_qty,
                    price=ticker.current_price * (1 + Decimal('0.05')),
                    status='FILLED'
                )
        
        self.stdout.write('Created demo orders')
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
