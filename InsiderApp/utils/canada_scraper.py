#InsiderApp\utils\canada_scraper.py
import requests
from bs4 import BeautifulSoup

def scrape_canadian_insider_filings(ticker):
    base_url = "https://www.sedi.ca/sedi/SVTItdController"
    params = {
        "locale": "en_CA",
        "pageName": "issuerTransaction",
        "issuerNumber": ticker
    }
    
    response = requests.get(base_url, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    transactions = []
    table = soup.find('table', class_='list')
    if table:
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 6:
                transaction = {
                    'date': cols[0].text.strip(),
                    'insider_name': cols[1].text.strip(),
                    'security': cols[2].text.strip(),
                    'nature': cols[3].text.strip(),
                    'number': cols[4].text.strip(),
                    'price': cols[5].text.strip()
                }
                transactions.append(transaction)
    
    return transactions
