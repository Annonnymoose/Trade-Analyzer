// Real-Time Market Data WebSocket Handler
class MarketDataSocket {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000;
        this.isConnected = false;
        this.subscribers = new Map();
        
        this.connect();
    }
    
    connect() {
        try {
            // Using a mock WebSocket for demo - replace with real market data provider
            this.socket = new WebSocket('wss://stream.tradingview.com/socket.io/');
            
            this.socket.onopen = () => {
                console.log('Market data connection established');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
                this.subscribeToWatchlist();
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMarketData(data);
                } catch (error) {
                    console.error('Failed to parse market data:', error);
                }
            };
            
            this.socket.onclose = () => {
                console.log('Market data connection closed');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.scheduleReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('Failed to establish WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    handleMarketData(data) {
        if (data.type === 'price_update') {
            this.updatePrice(data.symbol, data.price, data.change, data.changePercent);
        } else if (data.type === 'trade') {
            this.updateTrade(data.symbol, data.price, data.volume);
        } else if (data.type === 'news') {
            this.updateNews(data);
        }
    }
    
    updatePrice(symbol, price, change, changePercent) {
        // Update price displays
        const priceElements = document.querySelectorAll(`[data-symbol="${symbol}"] .price`);
        const changeElements = document.querySelectorAll(`[data-symbol="${symbol}"] .change`);
        
        priceElements.forEach(element => {
            element.textContent = `$${price.toFixed(2)}`;
            this.animateChange(element);
        });
        
        changeElements.forEach(element => {
            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = change >= 0 ? '▲' : '▼';
            
            element.className = `change ${changeClass}`;
            element.innerHTML = `${changeIcon} $${Math.abs(change).toFixed(2)} (${changePercent.toFixed(2)}%)`;
            this.animateChange(element);
        });
        
        // Update charts if visible
        this.updateChart(symbol, price);
        
        // Trigger notifications for significant changes
        if (Math.abs(changePercent) > 5) {
            this.showPriceAlert(symbol, price, changePercent);
        }
    }
    
    updateTrade(symbol, price, volume) {
        const tradeElements = document.querySelectorAll(`[data-symbol="${symbol}"] .last-trade`);
        
        tradeElements.forEach(element => {
            element.innerHTML = `
                <small class="text-muted">
                    Last: $${price.toFixed(2)} 
                    Vol: ${this.formatVolume(volume)}
                </small>
            `;
        });
    }
    
    updateChart(symbol, price) {
        const chartElement = document.querySelector(`#chart-${symbol}`);
        if (chartElement && window.charts && window.charts[symbol]) {
            const chart = window.charts[symbol];
            const now = Math.floor(Date.now() / 1000);
            
            chart.update({
                time: now,
                close: price,
                high: price,
                low: price,
                open: price
            });
        }
    }
    
    animateChange(element) {
        element.classList.add('price-flash');
        setTimeout(() => {
            element.classList.remove('price-flash');
        }, 1000);
    }
    
    showPriceAlert(symbol, price, changePercent) {
        const alertType = changePercent > 0 ? 'success' : 'danger';
        const alertIcon = changePercent > 0 ? '📈' : '📉';
        
        this.showToast(
            `${alertIcon} ${symbol}`,
            `Price moved ${changePercent.toFixed(2)}% to $${price.toFixed(2)}`,
            alertType
        );
    }
    
    showToast(title, message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type} show`;
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
    
    subscribeToWatchlist() {
        // Get current watchlist symbols
        const watchlistSymbols = Array.from(document.querySelectorAll('[data-symbol]'))
            .map(el => el.dataset.symbol)
            .filter((symbol, index, arr) => arr.indexOf(symbol) === index);
        
        if (this.isConnected && watchlistSymbols.length > 0) {
            const subscribeMessage = {
                action: 'subscribe',
                symbols: watchlistSymbols
            };
            
            this.socket.send(JSON.stringify(subscribeMessage));
        }
    }
    
    subscribe(symbol) {
        if (this.isConnected) {
            const message = {
                action: 'subscribe',
                symbols: [symbol]
            };
            this.socket.send(JSON.stringify(message));
        }
    }
    
    unsubscribe(symbol) {
        if (this.isConnected) {
            const message = {
                action: 'unsubscribe',
                symbols: [symbol]
            };
            this.socket.send(JSON.stringify(message));
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            const statusConfig = {
                connected: { text: 'Live', class: 'badge bg-success', icon: '🟢' },
                disconnected: { text: 'Offline', class: 'badge bg-danger', icon: '🔴' },
                error: { text: 'Error', class: 'badge bg-warning', icon: '🟡' },
                connecting: { text: 'Connecting...', class: 'badge bg-info', icon: '🟡' }
            };
            
            const config = statusConfig[status] || statusConfig.disconnected;
            statusElement.className = config.class;
            statusElement.innerHTML = `${config.icon} ${config.text}`;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting');
            
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, this.reconnectInterval * this.reconnectAttempts);
        }
    }
    
    formatVolume(volume) {
        if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        }
        return volume.toString();
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Market Hours Helper
class MarketHours {
    constructor() {
        this.updateMarketStatus();
        setInterval(() => this.updateMarketStatus(), 60000); // Update every minute
    }
    
    updateMarketStatus() {
        const now = new Date();
        const easternTime = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
        const hour = easternTime.getHours();
        const day = easternTime.getDay();
        
        // Market is open Monday-Friday 9:30 AM - 4:00 PM ET
        const isWeekday = day >= 1 && day <= 5;
        const isMarketHours = hour >= 9.5 && hour < 16;
        const isOpen = isWeekday && isMarketHours;
        
        this.updateMarketStatusDisplay(isOpen);
    }
    
    updateMarketStatusDisplay(isOpen) {
        const statusElements = document.querySelectorAll('.market-status');
        statusElements.forEach(element => {
            element.className = `market-status ${isOpen ? 'open' : 'closed'}`;
            element.textContent = isOpen ? 'Market Open' : 'Market Closed';
        });
    }
}

// Portfolio Performance Calculator
class PortfolioCalculator {
    constructor() {
        this.positions = new Map();
        this.totalValue = 0;
        this.totalCost = 0;
        this.totalGainLoss = 0;
        this.totalGainLossPercent = 0;
    }
    
    updatePosition(symbol, shares, currentPrice, avgCost) {
        const position = {
            symbol,
            shares,
            currentPrice,
            avgCost,
            marketValue: shares * currentPrice,
            costBasis: shares * avgCost,
            gainLoss: (currentPrice - avgCost) * shares,
            gainLossPercent: ((currentPrice - avgCost) / avgCost) * 100
        };
        
        this.positions.set(symbol, position);
        this.calculateTotals();
        this.updatePortfolioDisplay();
    }
    
    calculateTotals() {
        this.totalValue = 0;
        this.totalCost = 0;
        
        for (const position of this.positions.values()) {
            this.totalValue += position.marketValue;
            this.totalCost += position.costBasis;
        }
        
        this.totalGainLoss = this.totalValue - this.totalCost;
        this.totalGainLossPercent = this.totalCost > 0 ? (this.totalGainLoss / this.totalCost) * 100 : 0;
    }
    
    updatePortfolioDisplay() {
        const elements = {
            totalValue: document.getElementById('portfolio-total-value'),
            totalGainLoss: document.getElementById('portfolio-gain-loss'),
            totalGainLossPercent: document.getElementById('portfolio-gain-loss-percent')
        };
        
        if (elements.totalValue) {
            elements.totalValue.textContent = `$${this.totalValue.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }
        
        if (elements.totalGainLoss) {
            const gainLossClass = this.totalGainLoss >= 0 ? 'text-success' : 'text-danger';
            const gainLossIcon = this.totalGainLoss >= 0 ? '▲' : '▼';
            
            elements.totalGainLoss.className = gainLossClass;
            elements.totalGainLoss.innerHTML = `${gainLossIcon} $${Math.abs(this.totalGainLoss).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }
        
        if (elements.totalGainLossPercent) {
            const percentClass = this.totalGainLossPercent >= 0 ? 'text-success' : 'text-danger';
            elements.totalGainLossPercent.className = percentClass;
            elements.totalGainLossPercent.textContent = `(${this.totalGainLossPercent.toFixed(2)}%)`;
        }
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize market data socket
    window.marketSocket = new MarketDataSocket();
    
    // Initialize market hours tracker
    window.marketHours = new MarketHours();
    
    // Initialize portfolio calculator
    window.portfolioCalculator = new PortfolioCalculator();
    
    // Add price flash animation CSS
    const style = document.createElement('style');
    style.textContent = `
        .price-flash {
            animation: priceFlash 1s ease-in-out;
        }
        
        @keyframes priceFlash {
            0% { background-color: transparent; }
            50% { background-color: #ffc107; }
            100% { background-color: transparent; }
        }
    `;
    document.head.appendChild(style);
    
    // Mock data for demonstration
    setTimeout(() => {
        if (window.marketSocket && window.marketSocket.isConnected) {
            // Simulate price updates
            setInterval(() => {
                const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'];
                const symbol = symbols[Math.floor(Math.random() * symbols.length)];
                const price = 100 + Math.random() * 200;
                const change = (Math.random() - 0.5) * 10;
                const changePercent = (change / price) * 100;
                
                window.marketSocket.updatePrice(symbol, price, change, changePercent);
            }, 3000);
        }
    }, 2000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.marketSocket) {
        window.marketSocket.disconnect();
    }
});
