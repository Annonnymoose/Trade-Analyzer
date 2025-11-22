from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Ticker(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=20)
    sector = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    volume = models.BigIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    is_index = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.symbol} - {self.name}"

class PriceBar(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='price_bars')
    date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.IntegerField()

    class Meta:
        unique_together = ('ticker', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.ticker.symbol} - {self.date}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_items')
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='watchlist_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'ticker')

    def __str__(self):
        return f"{self.user.username} - {self.ticker.symbol}"

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    STATUS_CHOICES = [
        ('FILLED', 'Filled'),
        ('CANCELED', 'Canceled'),
        ('PENDING', 'Pending'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=4, choices=ORDER_TYPE_CHOICES)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_type} {self.quantity} {self.ticker.symbol} @ {self.price}"
