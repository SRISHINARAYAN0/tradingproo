# InsiderApp/utils/stock_data.py

import yfinance as yf
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_company_info(ticker):
    logger.info(f"Fetching company info for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        logger.info(f"Raw info data: {info}")
        
        return {
            'name': info.get('longName', 'N/A'),
            'symbol': info.get('symbol', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'country': info.get('country', 'N/A'),
            'exchange': info.get('exchange', 'N/A'),
            'currency': info.get('currency', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'beta': info.get('beta', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            '50_day_moving_average': info.get('fiftyDayAverage', 'N/A'),
            'trailing_eps': info.get('trailingEps', 'N/A'),
            'total_revenue': info.get('totalRevenue', 'N/A'),
            'profit_margins': info.get('profitMargins', 'N/A'),
            'operating_margins': info.get('operatingMargins', 'N/A'),
            'return_on_equity': info.get('returnOnEquity', 'N/A'),
            'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', 'N/A'),
            'revenue_growth': info.get('revenueGrowth', 'N/A'),
            'shares_outstanding': info.get('sharesOutstanding', 'N/A'),
            'book_value': info.get('bookValue', 'N/A'),
            'price_to_book': info.get('priceToBook', 'N/A'),
        }
    except Exception as e:
        logger.error(f"Error fetching company info for {ticker}: {str(e)}")
        return {}


def get_stock_chart_data(ticker, period='1y', transactions=None):
    logger.info(f"Fetching stock chart data for {ticker} over {period}")
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        
        if history.empty:
            logger.warning(f"No historical data available for {ticker}")
            return None
        
        dates = history.index.strftime('%Y-%m-%d').tolist()
        prices = history['Close'].tolist()
        volumes = history['Volume'].tolist()
        
        transaction_data = []
        if transactions:
            for transaction in transactions:
                trade_date = transaction.get('filingDate')
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
                if trade_date and trade_date.strftime('%Y-%m-%d') in dates:
                    index = dates.index(trade_date.strftime('%Y-%m-%d'))
                    transaction_data.append({
                        'x': trade_date.strftime('%Y-%m-%d'),
                        'y': prices[index],
                        'type': 'buy' if transaction.get('tradeType') in ['P', 'A'] else 'sell',
                        'shares': transaction.get('qty'),
                        'price': transaction.get('price'),
                        'insiderName': transaction.get('insiderName'),
                        'title': transaction.get('title')
                    })
        
        logger.info(f"Fetched {len(dates)} data points and {len(transaction_data)} transactions for {ticker}")
        return {
            'dates': dates,
            'prices': prices,
            'volumes': volumes,
            'transactions': transaction_data
        }
    except Exception as e:
        logger.error(f"Error fetching stock chart data for {ticker}: {str(e)}")
        return None


def get_latest_price(ticker):
    logger.info(f"Fetching latest price for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        latest_data = stock.history(period='1d')
        if not latest_data.empty:
            latest_price = latest_data['Close'].iloc[-1]
            logger.info(f"Latest price for {ticker}: {latest_price}")
            return latest_price
        else:
            logger.warning(f"No latest price data available for {ticker}")
            return None
    except Exception as e:
        logger.error(f"Error fetching latest price for {ticker}: {str(e)}")
        return None

def get_historical_data(ticker, start_date, end_date):
    logger.info(f"Fetching historical data for {ticker} from {start_date} to {end_date}")
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(start=start_date, end=end_date)
        
        data = []
        for date, row in history.iterrows():
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
        
        logger.info(f"Fetched {len(data)} historical data points for {ticker}")
        return data
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
        return []

def calculate_moving_average(ticker, window=50):
    logger.info(f"Calculating {window}-day moving average for {ticker}")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window * 2)
        
        stock = yf.Ticker(ticker)
        history = stock.history(start=start_date, end=end_date)
        
        ma = history['Close'].rolling(window=window).mean()
        
        # Only return the last value (current MA)
        current_ma = ma.iloc[-1] if not ma.empty else None
        
        logger.info(f"{window}-day moving average for {ticker}: {current_ma}")
        return current_ma
    except Exception as e:
        logger.error(f"Error calculating moving average for {ticker}: {str(e)}")
        return None
