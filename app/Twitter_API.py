# Module Imports
import OpenAI_API

# Library Imports
import tweepy
import datetime
import os

class Twitter_API:
    
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN', os.getenv('TWITTER_BEARER_TOKEN')),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN', os.getenv('TWITTER_ACCESS_TOKEN')),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET', os.getenv('TWITTER_ACCESS_TOKEN_SECRET')),
            consumer_key=os.getenv('TWITTER_API_KEY', os.getenv('TWITTER_API_KEY')),
            consumer_secret=os.getenv('TWITTER_API_SECRET', os.getenv('TWITTER_API_SECRET')),
            return_type=dict
        )

    def post_to_twitter(self, tweet: str):
        if len(tweet) > 280:
            print(f"Error: Tweet is {len(tweet)} characters. X limit is 280.")
            return
        try:
            self.client.create_tweet(text=tweet)
            print("Successfully posted main tweet.")
        except Exception as e:
            with open('./logs/logs.txt', 'a') as f:
                f.write(f'{datetime.date.today()} - Post Error: {e}\n')
            print(f"Failed to post tweet: {e}")

    def respond_to_mentions(self):
        print("Checking for mentions...")
        
        if not os.path.exists('./logs/mentions.txt'):
            os.makedirs('./logs', exist_ok=True)
            open('./logs/mentions.txt', 'w').close()

        try:
            response = self.client.search_recent_tweets(
                query='@WSB_Journal', 
                max_results=os.getenv('TWITTER_MAX_QUERY_RESULTS_FOR_MENTIONS')
            )

            if 'data' not in response or not response['data']:
                print("No new mentions found. Skipping...")
                return

            with open('./logs/mentions.txt', 'r+') as f:
                mentions_history = f.read()
                
                for tweet in response['data']:
                    tweet_id = str(tweet['id'])
                    
                    if tweet_id not in mentions_history:
                        print(f"Replying to tweet ID: {tweet_id}")
                        reply_text = OpenAI_API.reply_to_tweet(tweet['text'])
                        
                        self.client.create_tweet(
                            text=reply_text,
                            in_reply_to_tweet_id=tweet_id
                        )
                        
                        f.write(tweet_id + '\n')
                        print(f"Successfully replied to {tweet_id}")

        except tweepy.TooManyRequests:
            print("Twitter Rate Limit Reached. The bot will skip mentions for 15 minutes.")
            return 
            
        except Exception as e:
            print(f"Unexpected error in mentions: {e}")
            return
        
# Manually trigger mention response for testing
if __name__ == '__main__':
    bot = Twitter_API()
    bot.respond_to_mentions()