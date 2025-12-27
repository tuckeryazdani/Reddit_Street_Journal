This version cleans up the formatting, adds a clear structure, and adopts a "developer-to-developer" tone. It sounds like a project you built, owned, and are proud of, rather than a generated technical manual.

📈 Reddit Street Journal
Turning Subreddit Hype into Actionable Market Insights
I built the Reddit Street Journal to bridge the gap between social media "noise" and actual market indicators. It’s a fully autonomous, containerized data pipeline that scrapes retail investor sentiment, filters it through a custom seasonality heuristic, and uses AI to share those insights with the world.

🧠 How it Works
The system is designed to be completely hands-off. Once a week, it executes a three-stage pipeline:

1. Data Ingestion & Mapping
Dynamic Ticker Resolution: I use BeautifulSoup to scrape Wikipedia for the current S&P 500 list. This maps company names to tickers so the bot actually understands that "Apple" and "AAPL" are the same thing.

Reddit Scraping: Using the PRAW API, the script scans top financial subreddits for high-frequency mentions and emerging trends.

Smart Caching: To avoid getting rate-limited (and to keep things fast), I implemented a local JSON caching system that manages data expiration.

2. Analysis & AI Logic
Seasonality Engine: This isn't just a mention counter. The bot adjusts sentiment scores based on the time of year—for example, giving extra weight to travel stocks in the summer or retail in Q4.

GPT-4o Commentary: Raw data is fed into OpenAI's GPT-4o to generate snarky, human-like financial commentary that fits the unique culture of retail investing forums.

3. Automated Distribution
Social Engagement: The bot autonomously tweets summaries via the X (Twitter) API and can even reply to users who mention the account.

Web Dashboard Sync: Every successful run triggers a Git automation script that pushes the latest data directly to my personal portfolio site.

🚀 The Tech Stack
I chose these tools to keep the project "Serverless" and cost-effective:

Cloud: Deployed as a Cloud Run Job on Google Cloud (GCP).

Automation: Scheduled via Cloud Scheduler (CRON) to run every Monday at 9:00 AM.

Containerization: Fully Dockerized to ensure it runs the same in the cloud as it does on my laptop.

Security: API keys and secrets are managed via .env files and Google Secret Manager.

🛠️ Local Setup
If you want to run this locally, you'll need to grab your own API keys for Reddit, Twitter, and OpenAI.

Bash

# Clone the repo
git clone https://github.com/tuckeryazdani/The-Reddit-Street-Journal.git
cd The-Reddit-Street-Journal

# Setup your environment variables
touch .env # Add your keys here

# Build and run with Docker
docker build -t reddit-journal .
docker run --env-file .env reddit-journal

# Build and Run with Docker
docker build -t reddit-journal .
docker run --env-file .env reddit-journal
