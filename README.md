📈 Reddit Street Journal
Autonomous Sentiment Analysis & Market Forecasting Pipeline

Reddit Street Journal is a fully containerized data pipeline that bridges social media "hype" with fundamental market indicators. It autonomously scrapes retail investor sentiment from Reddit, cross-references it with S&P 500 equities, and applies a seasonality heuristic to forecast stock performance. The results are published via an interactive AI persona on X (Twitter) and synced to a live web dashboard.

🛠️ System Architecture
1. Data Ingestion & Mapping
Dynamic Ticker Resolution: Scrapes Wikipedia via BeautifulSoup to map S&P 500 company names to their official tickers, ensuring context-aware sentiment analysis.

Social Scraping: Utilizes the Reddit API (PRAW) to monitor specific financial subreddits for high-frequency mentions and emerging trends.

Intelligent Caching: Implements a local JSON-based caching system to minimize external requests and respect API rate limits.

2. Analysis & Heuristics
Seasonality Engine: Adjusts sentiment scores based on historical sector performance (e.g., boosting airline/travel weights during summer months).

AI Commentary: Passes raw sentiment data to OpenAI’s GPT-4o to generate snarky, human-like financial insights tailored to the subreddit's unique culture.

3. Automated Distribution
Social Engagement: Autonomously posts summaries to X (Twitter) and utilizes the Twitter API to engage with followers in real-time.

Web Sync: Automatically publishes the latest findings to a personal portfolio site via Git automation.

🚀 Deployment
The application is built for modern cloud environments and is fully Dockerized.

Infrastructure
Google Cloud Platform: Deployed as a Cloud Run Job for serverless, cost-efficient execution.

Cloud Scheduler: Configured via CRON to run every Monday at 9:00 AM.

Secret Management: Securely handles API keys using .env files and Google Secret Manager.

Local Setup
Bash

# Clone the repository
git clone https://github.com/yourusername/Reddit_Street_Journal.git

# Setup Environment Variables
cp .env.example .env

# Build and Run with Docker
docker build -t reddit-journal .
docker run --env-file .env reddit-journal
📊 Technical Challenges Overcome
Port 8080 Conflicts: Migrated from Cloud Run Services to Cloud Run Jobs to better handle non-web scraping workloads.

Memory Optimization: Optimized container resources (2GB RAM) to handle large Python libraries like pandas and yfinance.

Rate Limiting: Developed a custom caching layer for Wikipedia and Reddit data to ensure 100% uptime within free-tier API limits.
