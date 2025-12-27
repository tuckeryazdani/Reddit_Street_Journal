# Module Imports
from Reddit_API import Reddit_API
from Twitter_API import Twitter_API
import stock_data
# Library Imports
import pandas as pd
import datetime
import pandas as pd

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def main():
    
    # Begin script.
    DESIRED_SUBREDDIT = r"wallstreetbets"
    # Get dictionary that converts company name to its ticker and also get top 500 companeis.
    COMPANY_NAME_TO_TICKER = stock_data.get_company_name_to_ticker_dict()
    
    # Initialize Reddit_API object to create a connection to the Reddit API.
    reddit_client = Reddit_API(COMPANY_NAME_TO_TICKER, 100)
    # Call the get_count_of_stock_mentions function to return a dictionary of stocks found and the number of times they were mentioned.
    stock_names_found = reddit_client.get_count_of_stock_mentions(DESIRED_SUBREDDIT)
    print(f'Stocks Found: {stock_names_found}')

    # Use the Yahoo Fiance API to determine how much these stocks have changed in the past 7 days. 
    stock_price_change = stock_data.get_stock_price_change(stock_names_found, COMPANY_NAME_TO_TICKER)
    print(f'Stock Changes: {stock_price_change}')

    # Find the stock with the most mentions, how many mentions it has, and how it is changing in the stock market.
    most_mentioned_stock = max(stock_names_found,key=stock_names_found.get)
    most_mentioned_stock_count = stock_names_found[most_mentioned_stock]
    most_mentioned_stock_price_delta = stock_price_change[most_mentioned_stock]
        
    # Using the requests library, make a request to a NASSDAQ URL for CSV data of the most mentioned stock.  
    seasonal_trends = stock_data.get_seasonal_trends(COMPANY_NAME_TO_TICKER[most_mentioned_stock])
    # Using the datetime library, identify what is the current season of today.
    current_season = stock_data.identify_season(datetime.date.today())
    print(f'Seasonal Trends for {most_mentioned_stock}: {seasonal_trends}')
    print(f'Current Season: {current_season}')
    
    # Get average value of every season for the most mentioned stock.
    seasonal_avg = 0
    for season in seasonal_trends:
        seasonal_avg += seasonal_trends[season]
    seasonal_avg /= 4
    print(f'Seasonal Average for {most_mentioned_stock} is {seasonal_avg}.')

    # Create additional messages with information about the stocks seasonal performance for the tweet.
    if seasonal_trends[current_season] > seasonal_avg:
        seasonal_information = f'{most_mentioned_stock.title()} ({COMPANY_NAME_TO_TICKER[most_mentioned_stock]}) stock price tends to be higher in the {current_season}.'# by ${seasonal_trends[current_season] - seasonal_avg}.'
    else:
        seasonal_information = f'{most_mentioned_stock.title()} ({COMPANY_NAME_TO_TICKER[most_mentioned_stock]}) stock price tends to be lower in the {current_season}.'# by ${seasonal_trends[current_season] - seasonal_avg}.' 
    
    # Create additional messages with information about the stocks seasonal performance for the NEXT season for the tweet.
    next_season = list(seasonal_trends.keys())[(list(seasonal_trends.keys()).index(current_season)+1)%4]
    if seasonal_trends[next_season] > seasonal_trends[current_season]:
        seasonal_information += f'\nNext season ({next_season}) tends to be higher than {current_season}.'
    else:
        seasonal_information += f'\nNext season ({next_season}) tends to be lower than {current_season}.'
    
    # In development.:
        # stock_with_highest_delta = max(stockChanges.items(), key=lambda x: abs(x[1]))[0]
        # highest_delta_information = f'Highest Change in price: {stock_with_highest_delta.title()} {COMPANY_NAME_TO_TICKER[stock_with_highest_delta]} ${stockChanges[stock_with_highest_delta]}.'

    
    # Create tweet.
    tweet=f"""
Top trending stock on Wall Street Bets
({datetime.date.today()})

Stock: {most_mentioned_stock.title()}
{str(most_mentioned_stock_count)} mention(s) 

${most_mentioned_stock_price_delta} change in value the past 7 days.
{seasonal_information}
"""
    print(f'Tweet length: {len(tweet)}')
    print(f'Tweet:\n {tweet}')
    
    # Initialize Twitter_API object to create a connection to the Twitter API.
    twitter_client = Twitter_API()
    # Post the tweet we created to Twitter. (See logs.txt for errors)
    twitter_client.post_to_twitter(tweet)
    # (For fun only) Respond to tweets that tag "@WSB_Journal" with a funny response mimicing someone from the community. 
    twitter_client.respond_to_mentions()
    
    return tweet

if __name__ == '__main__':
    tweet = main()
    print(tweet)