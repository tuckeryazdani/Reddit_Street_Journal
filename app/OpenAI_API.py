import os
import time
from openai import OpenAI, RateLimitError

# Initialize the modern client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def reply_to_tweet(tweet: str):
    """
    Uses gpt-4o-mini to generate a funny response. 
    Handles rate limits with a loop instead of recursion.
    """
    system_prompt = os.getenv('OPENAI_CHARACTER')
    
    while True:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", # New, faster, and smarter model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Respond to this tweet: {tweet}"},
                ],
                max_tokens=150 # Keeps responses concise for X/Twitter
            )
            
            result = response.choices[0].message.content
            print(f"Responding to tweet:\n{tweet}")
            print(f"Response:\n{result}")
            return result

        except RateLimitError:
            print("Rate limit reached. Sleeping for 60 seconds...")
            time.sleep(60)
            continue # Try the loop again
            
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise e