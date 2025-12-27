The Reddit Street Journal
The Reddit Street Journal is a Python-powered data pipeline that tracks trending stocks discussed in various Reddit communities. It aggregates stock mentions, pulls live pricing data from Yahoo Finance, generates AI-driven insights, and shares them automatically on Twitter, offering a fully automated snapshot of what retail traders are buzzing about.

Key Features
📈 Reddit Stock Frequency: Extracts and ranks the most-mentioned tickers from Reddit communities using Reddit’s API.

💹 Real-Time Price Fetching: Retrieves up-to-date stock prices via the Yahoo Finance API.

🤖 AI-Generated Insights: Summarizes trending stocks using GPT-based language models for clean, readable updates.

📊 Data Visualization: Charts and plots display sentiment and volume trends over time.

🔁 Automated Posting: Shares weekly insights directly to Twitter, no manual input needed.

⏰ Scheduled Workflows: Runs on a regular cadence using containerized scheduled tasks.

Installation & Setup
Clone the repository

Bash

git clone https://github.com/tuckeryazdani/The-Reddit-Street-Journal.git
cd The-Reddit-Street-Journal
Configure Environment Variables Create a .env file in the root directory and add your API credentials. This file is used by Docker to securely pass your secrets to the application.

Plaintext

OPENAI_API_KEY=your_openai_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
TWITTER_API_KEY=your_twitter_key
Build the Docker Image

Bash

docker build -t reddit-street-journal .
Run the Bot Run the following command to start the automated pipeline using your environment variables:

Bash

docker run --env-file .env reddit-street-journal
Alternative: Docker Compose
For a one-command setup that handles building and environment configuration automatically:

Bash

docker-compose up --build
