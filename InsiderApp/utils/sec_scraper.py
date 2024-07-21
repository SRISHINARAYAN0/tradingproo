# InsiderApp/utils/sec_scraper.py

from sec_api import InsiderTradingApi
import logging
import pandas as pd
import math
import numpy as np
import traceback
import json
import re

logger = logging.getLogger(__name__)

API_KEY = "9362e757e1f751b0a98b03395ff742c0ff61f47a666560de4a26d92bcfb1c402"
insiderTradingApi = InsiderTradingApi(API_KEY)

TRANSACTION_TYPES = {
    'P': 'Purchase',
    'S': 'Sale',
    'A': 'Grant',
    'D': 'Sale to Issuer',
    'F': 'Pay Exercise',
    'I': 'Discretionary',
    'M': 'Exercise/Convert',
    'C': 'Convert',
    'E': 'Expire Short',
    'H': 'Expire Hold',
    'O': 'Out-of-Money',
    'X': 'In-Money',
    'G': 'Gift',
    'L': 'Small Acquisition',
    'W': 'Will',
    'Z': 'Trust',
    'J': 'Other',
    'K': 'Equity Swap',
    'U': 'UOP Disp',
    'V': 'Vol Report'
}

def format_number(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        logger.warning(f"Unable to format number: {value}")
        return value

def get_nested_value(data, keys):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        elif isinstance(data, list) and len(data) > 0:
            data = data[0].get(key, {}) if isinstance(data[0], dict) else {}
        else:
            return None
    return data if data != {} else None

def find_title_in_text(text):
    title_patterns = [
        r"(Chief\s+[\w\s]+(?:Officer|Executive))",
        r"((?:Executive\s+)?Vice\s+President(?:\s+[\w\s]+)?)",
        r"(President(?:\s+[\w\s]+)?)",
        r"(Director(?:\s+[\w\s]+)?)",
        r"(Chairman(?:\s+[\w\s]+)?)",
        r"((?:Senior|Junior)\s+[\w\s]+)",
        r"((?:Chief|Principal|Executive|Senior|Junior)\s+[\w\s]+)"
    ]
    
    for pattern in title_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0].strip()
    
    return None

def get_title(filing):
    potential_titles = [
        get_nested_value(filing, ["reportingOwner", "officerTitle"]),
        get_nested_value(filing, ["reportingOwner", "title"]),
        get_nested_value(filing, ["reportingOwner", 0, "officerTitle"]),
        get_nested_value(filing, ["reportingOwner", 0, "title"]),
        filing.get("reportingOwnerTitle"),
        filing.get("ownerOfficerTitle")
    ]
    
    logger.debug(f"Potential titles found: {potential_titles}")
    
    title = next((t for t in potential_titles if t), None)
    
    if not title:
        title = find_title_in_text(json.dumps(filing))
        logger.debug(f"Title found in text: {title}")

    logger.debug(f"Final title: {title}")
    return title or "N/A"

def flatten_filing(filing):
    transactions = []

    try:
        if isinstance(filing, str):
            try:
                filing = json.loads(filing)
            except json.JSONDecodeError:
                logger.error(f"Unable to parse filing as JSON: {filing[:100]}...")
                return []

        logger.debug(f"Full filing structure: {json.dumps(filing, indent=2)}")

        title = get_title(filing)

        base_data = {
            "filingDate": filing.get("filedAt"),
            "ticker": filing.get("issuer", {}).get("tradingSymbol"),
            "insiderName": filing.get("reportingOwner", {}).get("name"),
            "title": title
        }

        logger.debug(f"Base data for filing: {base_data}")
        logger.debug(f"Title retrieved: {title}")

        if "transactions" not in filing.get("nonDerivativeTable", {}):
            logger.warning(f"No transactions found in filing for {base_data['ticker']}")
            return []

        for transaction in filing.get("nonDerivativeTable", {}).get("transactions", []):
            try:
                shares = int(float(transaction.get("amounts", {}).get("shares", 0)))
                share_price = float(transaction.get("amounts", {}).get("pricePerShare", 0))
                value = math.ceil(shares * share_price)
                
                shares_owned_following = int(float(transaction.get("postTransactionAmounts", {}).get("sharesOwnedFollowingTransaction", 0)))
                acquired_disposed_code = transaction.get("amounts", {}).get("acquiredDisposedCode")
                
                shares_owned_before = shares_owned_following - shares if acquired_disposed_code == "A" else shares_owned_following + shares
                
                if shares_owned_before > 0:
                    delta_own_percent = (shares / shares_owned_before) * 100
                    delta_own_str = f"+{delta_own_percent:.2f}%" if acquired_disposed_code == "A" else f"-{delta_own_percent:.2f}%"
                else:
                    delta_own_str = "N/A"

                trade_type_code = (transaction.get("coding", {}).get("transactionCode") or
                                   transaction.get("coding", {}).get("code") or
                                   transaction.get("transactionCode", "N/A"))
                trade_type = f"{trade_type_code} - {TRANSACTION_TYPES.get(trade_type_code, 'Unknown')}"

                entry = {
                    "tradeDate": transaction.get("datesAndDeadlines", {}).get("transactionDate"),
                    "tradeType": trade_type,
                    "price": f"${share_price:.2f}",
                    "qty": format_number(shares),
                    "owned": format_number(shares_owned_following),
                    "ΔOwn": delta_own_str,
                    "value": f"${format_number(value)}"
                }
                transactions.append({**base_data, **entry})
                logger.debug(f"Processed transaction: {entry}")
            except (KeyError, ValueError) as e:
                logger.warning(f"Error processing transaction: {str(e)}")
                logger.debug(f"Problematic transaction data: {transaction}")

    except Exception as e:
        logger.error(f"Error in flatten_filing: {str(e)}")
        logger.debug(f"Problematic filing data: {filing}")
        logger.debug(traceback.format_exc())

    return transactions

def flatten_filings(filings):
    flattened = []
    for filing in filings:
        flattened.extend(flatten_filing(filing))
    logger.debug(f"Total flattened transactions: {len(flattened)}")
    return flattened

def get_insider_transactions(ticker):
    logger.info(f"Getting insider transactions for {ticker}")
    try:
        insider_trades = insiderTradingApi.get_data({
            "query": f"issuer.tradingSymbol:{ticker}",
            "from": "0",
            "size": "50",
            "sort": [{"filedAt": {"order": "desc"}}]
        })

        logger.debug(f"Raw API response: {json.dumps(insider_trades, indent=2)}")

        if "transactions" not in insider_trades:
            logger.error(f"No transactions found for {ticker}.")
            return []

        transactions = flatten_filings(insider_trades.get("transactions", []))
        logger.debug(f"Flattened transactions: {transactions[:2]}")  # Log first two transactions

        df = pd.DataFrame(transactions)

        if df.empty:
            logger.warning(f"No valid transactions found for {ticker}.")
            return []

        logger.debug(f"DataFrame columns: {df.columns}")
        logger.debug(f"Sample row: {df.iloc[0] if not df.empty else 'Empty DataFrame'}")


        for date_field in ['filingDate', 'tradeDate']:
            df[date_field] = pd.to_datetime(df[date_field], errors='coerce', utc=True)

        # Ensure all required columns are present
        required_columns = ['filingDate', 'tradeDate', 'ticker', 'insiderName', 'title', 'tradeType', 'price', 'qty', 'owned', 'ΔOwn', 'value']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Column {col} not found in DataFrame. Adding with None values.")
                df[col] = None

        df = df.replace({np.nan: None, pd.NaT: None})

        df = df.sort_values('tradeDate', ascending=False, na_position='last')

        transactions_dict = df.to_dict('records')
        logger.info(f"Found {len(transactions_dict)} insider transactions for {ticker}")
        logger.debug(f"Sample transaction: {transactions_dict[0] if transactions_dict else 'No transactions'}")
        return transactions_dict
    except Exception as e:
        logger.error(f"Error fetching insider transactions for {ticker}: {str(e)}")
        logger.debug(traceback.format_exc())
        return []
