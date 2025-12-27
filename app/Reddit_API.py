import os
import logging
import praw
from collections import Counter
from dotenv import load_dotenv

# Initialize logging to help debug connection issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Reddit_API:
    def __init__(self, company_name_to_ticker: dict, post_scan_limit: int):
        # Ensure environment variables are loaded
        load_dotenv()
        
        # Validate critical credentials exist
        self._validate_env_vars()

        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD')
        )
        # Use a set for faster lookups and lowercase them once
        self.stocks = {stock.lower() for stock in company_name_to_ticker.keys()}
        self.post_scan_limit = post_scan_limit

    def _validate_env_vars(self):
        required = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    def get_count_of_stock_mentions(self, desired_subreddit: str) -> dict:
        """
        Scrapes Reddit for stock mentions using an optimized Counter and word matching.
        """
        stocks_mentioned = Counter()
        
        try:
            subreddit = self.reddit.subreddit(desired_subreddit)
            # Use replace_more(limit=0) to skip 'load more comments' and speed up scraping
            for submission in subreddit.hot(limit=self.post_scan_limit):
                submission.comments.replace_more(limit=0) 
                
                for comment in submission.comments.list():
                    body = comment.body.lower()
                    
                    # Optimization: Check if any stock keyword exists in the string 
                    # before iterating through the full stock list
                    for stock in self.stocks:
                        if stock in body:
                            stocks_mentioned[stock] += 1
                            
        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")
            return {}

        # Handle Meta/Facebook rebranding logic using dictionary methods
        self._merge_fb_to_meta(stocks_mentioned)

        return dict(stocks_mentioned)

    def _merge_fb_to_meta(self, counts: Counter):
        """Helper to consolidate Facebook mentions into Meta."""
        if "facebook" in counts:
            counts["meta"] += counts.pop("facebook")