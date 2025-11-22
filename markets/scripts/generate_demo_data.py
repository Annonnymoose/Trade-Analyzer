import json
import random
from datetime import datetime, timedelta
from decimal import Decimal

def generate_price_history(base_price, volatility, days, volume_base):
    """Generate realistic looking price history."""
    prices = []
    current_price = Decimal(str(base_price))
    current_date = datetime.now().date() - timedelta(days=days)
    
    for _ in range(days):
        # Generate daily price movement
        daily_volatility = float(current_price) * volatility
        open_price = float(current_price)
        close_price = open_price * (1 + random.uniform(-volatility, volatility))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, volatility/2))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, volatility/2))
        
        # Generate realistic volume
        base_volume = volume_base * (1 + random.uniform(-0.3, 0.3))
        if abs((close_price - open_price) / open_price) > volatility/2:
            base_volume *= 1.5  # Higher volume on bigger price moves
        
        prices.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "open": round(Decimal(str(open_price)), 2),
            "high": round(Decimal(str(high_price)), 2),
            "low": round(Decimal(str(low_price)), 2),
            "close": round(Decimal(str(close_price)), 2),
            "volume": int(base_volume)
        })
        
        current_price = Decimal(str(close_price))
        current_date += timedelta(days=1)
    
    return prices

# Configuration for each stock
STOCK_CONFIGS = {
    1: {"symbol": "RELIANCE", "base_price": 2800, "volatility": 0.015, "volume": 1500000},
    2: {"symbol": "TCS", "base_price": 3400, "volatility": 0.012, "volume": 1000000},
    3: {"symbol": "HDFCBANK", "base_price": 1650, "volatility": 0.013, "volume": 2000000},
    4: {"symbol": "INFY", "base_price": 1550, "volatility": 0.014, "volume": 1200000},
    5: {"symbol": "BHARTIARTL", "base_price": 880, "volatility": 0.016, "volume": 1800000}
}

# Generate price bars for each stock
price_bars = []
pk_counter = 1

for ticker_id, config in STOCK_CONFIGS.items():
    history = generate_price_history(
        config["base_price"],
        config["volatility"],
        90,  # 90 days of history
        config["volume"]
    )
    
    for bar in history:
        price_bars.append({
            "model": "markets.pricebar",
            "pk": pk_counter,
            "fields": {
                "ticker": ticker_id,
                "date": bar["date"],
                "open": str(bar["open"]),
                "high": str(bar["high"]),
                "low": str(bar["low"]),
                "close": str(bar["close"]),
                "volume": bar["volume"]
            }
        })
        pk_counter += 1

# Save to file
with open('markets/fixtures/demo_pricebars.json', 'w') as f:
    json.dump(price_bars, f, indent=2)
