from tradingview_ta import TA_Handler, Interval

configurations = [
    {"exchange": "NASDAQ", "screener": "america"},
    {"exchange": "NYSE", "screener": "america"},
    {"exchange": "BINANCE", "screener": "crypto"},
]


def get_ticker_price(ticker):
    for configuration in configurations:
        try:
            handler = TA_Handler(
                symbol=ticker,
                exchange=configuration["exchange"],
                screener=configuration["screener"],
                interval=Interval.INTERVAL_1_MINUTE,
            )
            analysis = handler.get_analysis()
            return float(analysis.indicators["close"])
        except:
            continue

    raise ValueError(f"Could not find price for ticker: {ticker}")
