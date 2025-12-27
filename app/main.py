import wsb
import os
import logging
import datetime
from dotenv import load_dotenv

# Initialize logging for automation tracking
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Load environment variables from .env
load_dotenv()

# Configuration
WEBSITE_REPO_PATH = os.getenv('WEBSITE_REPO_PATH')
TWITTER_PATH = os.getenv('TWITTER_PATH')

def write_to_website(tweet: str):
    """
    Safely injects a new tweet into the HTML body.
    """
    if not TWITTER_PATH or not os.path.exists(TWITTER_PATH):
        logging.error(f"HTML path invalid or file missing: {TWITTER_PATH}")
        return

    # Read existing content safely
    with open(TWITTER_PATH, 'r', encoding='utf-8') as file:
        content = file.read()

    target = '<body>'
    if target not in content:
        logging.error("Could not find <body> tag in HTML.")
        return

    # Prepare HTML block
    formatted_tweet = tweet.replace('\n', '<br>')
    new_block = f'\n\n<br><br> <blockquote class="twitter-tweet">{formatted_tweet}</blockquote>'
    
    # Insert right after <body> tag
    index = content.index(target) + len(target)
    updated_content = content[:index] + new_block + content[index:]

    # Overwrite the file with updated content
    with open(TWITTER_PATH, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    logging.info("Successfully updated HTML file.")

def run_git(command):
    """Helper to run git commands and log status."""
    if os.system(command) != 0:
        logging.error(f"Git command failed: {command}")
        return False
    return True

def branch_and_push(tweet_content):
    """
    Creates a unique branch, commits changes, and pushes to remote.
    """
    # 1. Generate unique branch name based on date
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    new_branch = f"bot-post-{date_str}"
    
    logging.info(f"Setting up branch: {new_branch}")
    
    # 2. Ensure we start from the latest main
    run_git("git checkout main")
    run_git("git pull origin main")
    
    # 3. Create and switch to the new branch
    run_git(f"git checkout -b {new_branch}")
    
    # 4. Perform the website update
    write_to_website(tweet_content)
    
    # 5. Commit and Push
    run_git("git add --all")
    run_git(f'git commit -m "Automated update for {date_str}"')
    run_git(f"git push origin {new_branch}")
    
    logging.info(f"Pushed to {new_branch}. Open a Pull Request on GitHub to merge.")

if __name__ == '__main__':
    # Generate the tweet content using the existing wsb logic
    tweet = wsb.main()
    
    if WEBSITE_REPO_PATH and os.path.exists(WEBSITE_REPO_PATH):
        os.chdir(WEBSITE_REPO_PATH)
        branch_and_push(tweet)
    else:
        logging.error("WEBSITE_REPO_PATH not found. Ensure Docker volume is mounted.")