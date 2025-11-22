from django.core.management.base import BaseCommand
from markets.models import Ticker
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Load sample stock data'

    def handle(self, *args, **options):
        # Sample stock data
        stocks_data = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'sector': 'Technology', 'exchange': 'NASDAQ'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary', 'exchange': 'NASDAQ'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Consumer Discretionary', 'exchange': 'NASDAQ'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'sector': 'Technology', 'exchange': 'NASDAQ'},
            {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'sector': 'Financial Services', 'exchange': 'NYSE'},
            {'symbol': 'JNJ', 'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'exchange': 'NYSE'},
            {'symbol': 'V', 'name': 'Visa Inc.', 'sector': 'Financial Services', 'exchange': 'NYSE'},
            {'symbol': 'PG', 'name': 'Procter & Gamble Co.', 'sector': 'Consumer Staples', 'exchange': 'NYSE'},
            {'symbol': 'UNH', 'name': 'UnitedHealth Group Inc.', 'sector': 'Healthcare', 'exchange': 'NYSE'},
            {'symbol': 'HD', 'name': 'The Home Depot Inc.', 'sector': 'Consumer Discretionary', 'exchange': 'NYSE'},
            {'symbol': 'MA', 'name': 'Mastercard Inc.', 'sector': 'Financial Services', 'exchange': 'NYSE'},
            {'symbol': 'DIS', 'name': 'The Walt Disney Company', 'sector': 'Communication Services', 'exchange': 'NYSE'},
            {'symbol': 'ADBE', 'name': 'Adobe Inc.', 'sector': 'Technology', 'exchange': 'NASDAQ'},
            {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'sector': 'Communication Services', 'exchange': 'NASDAQ'},
            {'symbol': 'CRM', 'name': 'Salesforce Inc.', 'sector': 'Technology', 'exchange': 'NYSE'},
            {'symbol': 'PYPL', 'name': 'PayPal Holdings Inc.', 'sector': 'Financial Services', 'exchange': 'NASDAQ'},
            {'symbol': 'INTC', 'name': 'Intel Corporation', 'sector': 'Technology', 'exchange': 'NASDAQ'},
        ]

        # Create sample index data
        indices_data = [
            {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF', 'sector': 'ETF', 'exchange': 'NYSE', 'is_index': True},
            {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust', 'sector': 'ETF', 'exchange': 'NASDAQ', 'is_index': True},
            {'symbol': 'DIA', 'name': 'SPDR Dow Jones Industrial Average ETF', 'sector': 'ETF', 'exchange': 'NYSE', 'is_index': True},
        ]

        all_stocks = stocks_data + indices_data

        for stock_data in all_stocks:
            # Generate random price data
            base_price = random.uniform(20, 500)
            change = random.uniform(-10, 10)
            change_pct = (change / base_price) * 100
            
            ticker, created = Ticker.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults={
                    'name': stock_data['name'],
                    'sector': stock_data['sector'],
                    'exchange': stock_data['exchange'],
                    'price': Decimal(str(round(base_price, 2))),
                    'change': Decimal(str(round(change, 2))),
                    'change_pct': Decimal(str(round(change_pct, 2))),
                    'volume': random.randint(1000000, 100000000),
                    'is_index': stock_data.get('is_index', False)
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {ticker.symbol}')
                )
            else:
                # Update existing ticker with new random data
                ticker.price = Decimal(str(round(base_price, 2)))
                ticker.change = Decimal(str(round(change, 2)))
                ticker.change_pct = Decimal(str(round(change_pct, 2)))
                ticker.volume = random.randint(1000000, 100000000)
                ticker.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated existing {ticker.symbol}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded all stock data!')
        )
