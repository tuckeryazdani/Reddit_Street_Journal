import os
import logging
import praw
from collections import Counter
import datetime
# Initialize logging to help debug connection issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Reddit_API:
    def __init__(self, company_name_to_ticker: dict, post_scan_limit: int):
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

    def get_detailed_stock_mentions(self, desired_subreddit: str):
        """
        Returns a list of dictionaries containing every mention, the comment text, 
        and metadata for auditing.
        """
        all_mentions = []
        
        try:
            subreddit = self.reddit.subreddit(desired_subreddit)
            for submission in subreddit.hot(limit=self.post_scan_limit):
                submission.comments.replace_more(limit=0) 
                
                for comment in submission.comments.list():
                    body = comment.body.lower()
                    
                    for stock in self.stocks:
                        if stock in body:
                            # Save the full record
                            all_mentions.append({
                                'stock': stock,
                                'comment_body': comment.body,
                                'author': str(comment.author),
                                'created_at': datetime.datetime.fromtimestamp(comment.created_utc),
                                'post_title': submission.title
                            })
        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")
            return []

        return all_mentions

    def _merge_fb_to_meta(self, counts: Counter):
        """Helper to consolidate Facebook mentions into Meta."""
        if "facebook" in counts:
            counts["meta"] += counts.pop("facebook")