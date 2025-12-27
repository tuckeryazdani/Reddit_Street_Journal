The Reddit Street Journal

The Reddit Street Journal is a Python-powered data pipeline that tracks trending stocks discussed in various Reddit communities. It aggregates stock mentions, pulls live pricing data from Yahoo Finance, generates AI-driven insights, and shares them automatically on Twitter,  offering a fully automated snapshot of what retail traders are buzzing about.

Key Features

📈 Reddit Stock Frequency: Extracts and ranks the most-mentioned tickers from Reddit communities using Reddit’s API.

💹 Real-Time Price Fetching: Retrieves up-to-date stock prices via the Yahoo Finance API.

🤖 AI-Generated Insights: Summarizes trending stocks using GPT-based language models for clean, readable updates.

📊 Data Visualization: Charts and plots display sentiment and volume trends over time.

🔁 Automated Posting: Shares weekly insights directly to Twitter, no manual input needed.

⏰ Scheduled Workflows: Runs on a regular cadence using scheduled tasks.

Installation
1. Clone the repository
2. Replace your credentials in the .env file to set them as environment variables for Docker
3. docker build -t reddit-street-journal.
4. docker run --env-file .env reddit-street-journal
The Reddit Street Journal

