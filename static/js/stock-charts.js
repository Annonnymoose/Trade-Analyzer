// Sample OHLCV data for demonstration
const sampleData = {
    "data": [
        {
            "t": "2025-09-11",
            "o": 3250.50,
            "h": 3275.25,
            "l": 3225.75,
            "c": 3260.00,
            "v": 125000
        },
        {
            "t": "2025-09-10",
            "o": 3225.00,
            "h": 3260.50,
            "l": 3210.25,
            "c": 3250.50,
            "v": 115000
        },
        // Add more sample data points...
        {
            "t": "2025-09-01",
            "o": 3180.25,
            "h": 3205.75,
            "l": 3165.50,
            "c": 3195.25,
            "v": 98000
        }
    ]
};

// Chart configurations and setup
class StockCharts {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.charts = {};
        this.series = {};
    }

    // Initialize line chart
    initLineChart() {
        if (!this.container) return;

        this.charts.line = LightweightCharts.createChart(this.container, {
            layout: {
                background: { color: '#ffffff' },
                textColor: '#333',
            },
            grid: {
                vertLines: { color: '#f0f0f0' },
                horzLines: { color: '#f0f0f0' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#f0f0f0',
            },
            timeScale: {
                borderColor: '#f0f0f0',
                timeVisible: true,
            },
        });

        this.series.line = this.charts.line.addLineSeries({
            color: '#2962FF',
            lineWidth: 2,
        });

        // Format data for line chart
        const lineData = sampleData.data.map(item => ({
            time: item.t,
            value: item.c
        }));

        this.series.line.setData(lineData);
        this.charts.line.timeScale().fitContent();
    }

    // Initialize candlestick chart
    initCandlestickChart() {
        if (!this.container) return;

        this.charts.candlestick = LightweightCharts.createChart(this.container, {
            layout: {
                background: { color: '#ffffff' },
                textColor: '#333',
            },
            grid: {
                vertLines: { color: '#f0f0f0' },
                horzLines: { color: '#f0f0f0' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#f0f0f0',
            },
            timeScale: {
                borderColor: '#f0f0f0',
                timeVisible: true,
            },
        });

        this.series.candlestick = this.charts.candlestick.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        // Format data for candlestick chart
        const candleData = sampleData.data.map(item => ({
            time: item.t,
            open: item.o,
            high: item.h,
            low: item.l,
            close: item.c,
        }));

        this.series.candlestick.setData(candleData);
        this.charts.candlestick.timeScale().fitContent();
    }

    // Initialize volume chart
    initVolumeChart(containerId) {
        const volumeContainer = document.getElementById(containerId);
        if (!volumeContainer) return;

        this.charts.volume = LightweightCharts.createChart(volumeContainer, {
            height: 100,
            layout: {
                background: { color: '#ffffff' },
                textColor: '#333',
            },
            grid: {
                vertLines: { color: '#f0f0f0' },
                horzLines: { color: '#f0f0f0' },
            },
            rightPriceScale: {
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            timeScale: {
                visible: true,
                borderColor: '#f0f0f0',
            },
        });

        this.series.volume = this.charts.volume.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
        });

        // Format data for volume chart
        const volumeData = sampleData.data.map(item => ({
            time: item.t,
            value: item.v,
            color: item.c >= item.o ? '#26a69a' : '#ef5350',
        }));

        this.series.volume.setData(volumeData);
        this.charts.volume.timeScale().fitContent();
    }

    // Update time range for all charts
    updateTimeRange(range) {
        // Implement time range filtering logic here
        // range can be '1D', '1W', '1M', '3M', etc.
        console.log('Updating time range:', range);
    }

    // Resize charts
    resize() {
        Object.values(this.charts).forEach(chart => {
            chart.applyOptions({
                width: this.container.clientWidth,
            });
        });
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Line chart initialization
    const overviewChart = new StockCharts('lineChart');
    overviewChart.initLineChart();

    // Candlestick chart initialization
    const candlestickChart = new StockCharts('candlestickChart');
    candlestickChart.initCandlestickChart();
    candlestickChart.initVolumeChart('volumeChart');

    // Handle tab changes
    document.querySelectorAll('a[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', e => {
            if (e.target.getAttribute('href') === '#overview') {
                overviewChart.resize();
            } else if (e.target.getAttribute('href') === '#candlestick') {
                candlestickChart.resize();
            }
        });
    });

    // Handle time range buttons
    document.querySelectorAll('[data-range]').forEach(button => {
        button.addEventListener('click', e => {
            const range = e.target.dataset.range;
            
            // Update active button state
            document.querySelectorAll('[data-range]').forEach(btn => {
                btn.classList.remove('active');
            });
            e.target.classList.add('active');

            // Update charts
            overviewChart.updateTimeRange(range);
            candlestickChart.updateTimeRange(range);
        });
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        overviewChart.resize();
        candlestickChart.resize();
    });
});
