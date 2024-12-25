from tradingview_ta import TA_Handler, Interval

configs = [
    {"exchange": "NASDAQ", "screener": "america"},
    {"exchange": "NYSE", "screener": "america"},
    {"exchange": "BINANCE", "screener": "crypto"},
]


def get_ticker_price(ticker):
    for config in configs:
        try:
            handler = TA_Handler(
                symbol=ticker,
                exchange=config["exchange"],
                screener=config["screener"],
                interval=Interval.INTERVAL_1_MINUTE,
            )
            analysis = handler.get_analysis()
            return analysis.indicators["close"]
        except:
            continue

    raise ValueError(f"Could not find price for ticker: {ticker}")
