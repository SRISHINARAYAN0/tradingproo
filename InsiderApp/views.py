# InsiderApp/views.py

from django.shortcuts import render
from django.views import View
from .utils.sec_scraper import get_insider_transactions
from .utils.canada_scraper import scrape_canadian_insider_filings
from .utils.stock_data import get_company_info, get_stock_chart_data
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class InsiderTrackingView(View):
    template_name = 'results.html'

    def get(self, request):
        return render(request, 'index.html')

    def post(self, request):
        ticker = request.POST.get('ticker', '').upper()
        exchange = request.POST.get('exchange', 'NASDAQ')
        
        logger.info(f"Processing request for ticker: {ticker}, exchange: {exchange}")

        insider_transactions = []
        company_info = {}
        chart_data = None
        debug_info = {}

        try:
            if exchange == 'NASDAQ':
                insider_transactions = get_insider_transactions(ticker)
            else:  # Canadian exchange
                insider_transactions = scrape_canadian_insider_filings(ticker)
            
            logger.info(f"Fetched {len(insider_transactions)} insider transactions for {ticker}")
            
            #  debug info
            debug_info['insider_transactions'] = insider_transactions[:5]  # First 5 transactions
        except Exception as e:
            logger.error(f"Error fetching insider transactions for {ticker}: {str(e)}")
            debug_info['insider_transactions_error'] = str(e)

        try:
            company_info = get_company_info(ticker)
            logger.info(f"Fetched company info for {ticker}")
            
            # debug info
            debug_info['company_info'] = company_info
        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {str(e)}")
            debug_info['company_info_error'] = str(e)

        try:
            chart_data = get_stock_chart_data(ticker, transactions=insider_transactions)
            if chart_data and chart_data['dates']:
                logger.info(f"Fetched chart data for {ticker}: {len(chart_data['dates'])} data points")
                
                #  debug info
                debug_info['chart_data_sample'] = {
                    'dates': chart_data['dates'][:5],
                    'prices': chart_data['prices'][:5],
                    'transactions': chart_data['transactions'][:5]
                }
            else:
                logger.warning(f"No chart data available for {ticker}")
                chart_data = None
        except Exception as e:
            logger.error(f"Error fetching chart data for {ticker}: {str(e)}")
            chart_data = None
            debug_info['chart_data_error'] = str(e)

        context = {
            'ticker': ticker,
            'exchange': exchange,
            'insider_transactions': insider_transactions,
            'company_info': company_info,
            'chart_data': json.dumps(chart_data) if chart_data else None,
            'debug': settings.DEBUG,
            'debug_info': debug_info
        }

        logger.info(f"Rendering results for {ticker}")
        return render(request, self.template_name, context)
