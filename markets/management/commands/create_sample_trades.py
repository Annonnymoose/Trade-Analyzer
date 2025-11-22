from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from markets.models import Order, Ticker
from decimal import Decimal
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Create sample trading data'

    def handle(self, *args, **options):
        admin = User.objects.get(username='admin')
        
        # Sample trades for RELIANCE
        reliance = Ticker.objects.get(symbol='RELIANCE')
        # Buy 10 shares of Reliance
        Order.objects.create(
            user=admin,
            ticker=reliance,
            side='BUY',
            qty=10,
            price=Decimal('2800.00'),
            status='FILLED',
            created_at=datetime.now() - timedelta(days=5)
        )
        # Buy 5 more shares of Reliance
        Order.objects.create(
            user=admin,
            ticker=reliance,
            side='BUY',
            qty=5,
            price=Decimal('2850.00'),
            status='FILLED',
            created_at=datetime.now() - timedelta(days=3)
        )
        
        # Sample trades for TCS
        tcs = Ticker.objects.get(symbol='TCS')
        # Buy 8 shares of TCS
        Order.objects.create(
            user=admin,
            ticker=tcs,
            side='BUY',
            qty=8,
            price=Decimal('3400.00'),
            status='FILLED',
            created_at=datetime.now() - timedelta(days=4)
        )
        
        # Sample trades for INFY
        infy = Ticker.objects.get(symbol='INFY')
        # Buy 15 shares of Infosys
        Order.objects.create(
            user=admin,
            ticker=infy,
            side='BUY',
            qty=15,
            price=Decimal('1550.00'),
            status='FILLED',
            created_at=datetime.now() - timedelta(days=7)
        )
        # Sell 5 shares of Infosys at a profit
        Order.objects.create(
            user=admin,
            ticker=infy,
            side='SELL',
            qty=5,
            price=Decimal('1570.00'),
            status='FILLED',
            created_at=datetime.now() - timedelta(days=2)
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample trades'))
