# Library Imports
import os
import requests
import pandas as pd
import yfinance as yf
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import requests
from bs4 import BeautifulSoup
import time
import json

# Define where to save the data
CACHE_FILE = 'ticker_cache.json'
# How long to wait before re-scraping (e.g., 7 days in seconds)
CACHE_EXPIRATION = 604800 


# Constants for caching
CACHE_FILE = 'ticker_cache.json'
CACHE_EXPIRATION = 604800  # 7 days in seconds

def get_company_name_to_ticker_dict():
    # 1. Check if cache exists and is recent
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_EXPIRATION:
            print("Loading S&P 500 data from cache...")
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)

    # 2. If no cache or expired, do the scraping
    print("Cache expired or missing. Scraping Wikipedia...")
    URL = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        page = requests.get(URL, headers=headers)
        # FIX: "page" is now accessed here by passing page.text to BeautifulSoup
        soup = BeautifulSoup(page.text, 'html.parser')
        
        table = soup.find('table', {'id': 'constituents'}) 
        if not table:
            table = soup.find('table', {'class': 'wikitable'})

        if not table:
            raise Exception("Could not find the S&P 500 table on Wikipedia.")
        
        rows = table.findAll('tr')
        company_name_to_ticker = {}
        
        for row in rows[1:]:
            data = row.findAll('td')
            if len(data) >= 2:
                ticker = data[0].text.strip()
                name = data[1].text.strip()
                
                # Manual overrides for consistent naming
                if ticker == 'GOOGL': name = 'Google'
                elif ticker == 'META': name = 'Meta'
                
                company_name_to_ticker[name.lower()] = ticker.upper()

        # 3. Save to local file for next time
        with open(CACHE_FILE, 'w') as f:
            json.dump(company_name_to_ticker, f)
            
        return company_name_to_ticker

    except Exception as e:
        # Fallback: If scraping fails but an old cache exists, use it anyway
        if os.path.exists(CACHE_FILE):
            print(f"Scrape failed ({e}). Using expired cache as fallback.")
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        raise e
    
def get_stock_price_change(stocksFound, COMPANY_NAME_TO_TICKER):
    stock_price_change = {}
    for stock in stocksFound:
        ticker_symbol = COMPANY_NAME_TO_TICKER[stock]
        try:
            # Add a 0.5 second sleep to avoid rate limiting
            time.sleep(0.5) 
            ticker_history = yf.Ticker(ticker_symbol).history(period="7d")["Close"]
            
            if not ticker_history.empty:
                change = ticker_history.iloc[-1] - ticker_history.iloc[0]
                stock_price_change[stock] = float(round(change, 2))
            else:
                stock_price_change[stock] = 0.0
        except Exception:
            stock_price_change[stock] = 0.0
    return stock_price_change

import pandas as pd
from datetime import date

def identify_season(d: date) -> str:
    '''
    Given a date, this function returns the season.
    It uses the year 2000 (leap year) as a reference for seasonal boundaries.
    '''
    # Convert input to a comparable format in the year 2000
    # pd.Timestamp is flexible and accepts datetime.date objects
    d_ts = pd.Timestamp(d).replace(year=2000)

    # Define seasonal boundaries in a dictionary for cleaner lookup
    # Using tuples as (start_month, start_day)
    seasons = [
        ('Spring', pd.Timestamp(2000, 3, 20), pd.Timestamp(2000, 6, 20)),
        ('Summer', pd.Timestamp(2000, 6, 21), pd.Timestamp(2000, 9, 22)),
        ('Fall',   pd.Timestamp(2000, 9, 23), pd.Timestamp(2000, 12, 20))
    ]

    # Check Spring, Summer, and Fall ranges
    for name, start, end in seasons:
        if start <= d_ts <= end:
            return name

    # If it's not Spring, Summer, or Fall, it must be Winter (Dec 21 - Mar 19)
    return 'Winter'

def get_seasonal_trends(ticker : str):
    '''
    Get historical stock information using yfinance and determine the seasonal averages.
    '''
    # Fetch maximum available history for the stock
    df_history = yf.Ticker(ticker).history(period="max")
    
    if df_history.empty:
        print(f"Warning: No historical data found for {ticker}")
        return {'Winter': 0.0, 'Spring': 0.0, 'Summer': 0.0, 'Fall': 0.0}

    # Reset index to make 'Date' a column and keep only what we need
    df_history = df_history.reset_index()
    # Convert the Date column to be timezone-naive so it can be compared to your 2000-year dates
    df_history['Date'] = df_history['Date'].dt.tz_localize(None)
    df_history = df_history[['Date', 'Close']]

    # Identify the season for every date
    df_history['Season'] = df_history['Date'].apply(lambda x: identify_season(x))
    
    unique_years = df_history['Date'].dt.year.nunique()
    print(f'Unique Years of data found: {unique_years}')
    
    seasonal_values = {'Winter': None, 'Spring': None, 'Summer': None, 'Fall': None}
    
    # Find the smallest sample size among seasons to balance the average
    max_possible_row_count = min([len(df_history[df_history['Season'] == s]) for s in seasonal_values])
    
    # Calculate average seasonal stock price
    for season in seasonal_values:
        # We take the mean price across all years for that season
        avg_price = df_history[df_history['Season'] == season]['Close'].head(max_possible_row_count).mean()
        seasonal_values[season] = round(avg_price, 2)
    
    return seasonal_values