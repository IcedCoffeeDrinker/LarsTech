# Signal Backtracking

I recommend going for an algorithmic approach instead of training or fine-tuning an LLM model. Once an event is identified to be part of a certain signal, the news-stock relationship can be analyzed purely numerically. Extracting any confident value for certainty in correlation will include standard calculations such as estimating the beta, CAR, and abnormal returns.

## Example Datasets For Stocks

- Kaggle Datasets, e.g.:
    - Free, 20 years of US stock market history, daily, +7,000 companies
    - https://www.kaggle.com/datasets/tsaustin/us-historical-stock-prices-with-earnings-data
- Stooq Datasets, e.g.:
    - https://stooq.com/t/?i=518

## Example Datasets For Classical News Feeds / Alternative Data

- Kaggle Datasets, e.g.:
    - Daily Financial News for +6000 Stocks, 2009-2020
    - https://www.kaggle.com/datasets/miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests
- many more...

## Architecture

- Filter various historical news sources for a specific signal (e.g. medication x reached stage y)
- For each event, pull the company's stock data before and after the event
- Compute abnormal returns and CAR (referencing entire sector) - Estimate beta
- Calculate a score for signal-market correlation for the signal (take some average of all events)
- Evaluate certainty and strength of market shifts due to the signal based on correlation value/s
- → We might add more complicated models later, ergo multiple values for correlation

# Trading System

## Architecture (POC, starting simple)

- Take in signal sources 24/7 (e.g. newsfeeds or pharma-sites)
- Algorithmically filter the sources for keywords
- (Run an information-primer model that researches important information surrounding the event and creates a report) - optional
- Run evaluation model
    - Feed the alternative data (+ report) and calculated signal-market correlation information
    - Model returns stock prediction: direction, magnitude, duration, confidence
- Decide buy(, buy put, buy call) + duration either through:
    - Algorithmic calculations of values returned by evaluation model
    - Let the previous agent also make a decision on the final action
    - Additionally: don't define a period after which is sold, instead track any news and market information on the investment periodically. The agent decides when to sell.
- Track all investment data and stop / involve a human on repeated bad performance via a Telegram / Slack bot

# Inference Options

- Local:
    - RTX A6000 (48GB VRAM)
        - ~5,000 Euro for used parts
        - ~120 Euro / Month
- Cloud:
    - Runpod A100 PCIe (80GB VRAM, 117GB RAM)
        - ~900 Euro / Month
    - Runpod RTX A6000 (48 GB VRAM, 50GB RAM)
        - ~355 Euro / Month
- API:
    - 3 Euro / Million Tokens for smaller models
    - 15 Euro / Million Tokens for larger models
        - (3 Euro) cheaper than Runpod A6000, if Runpod load is below ~70 percent (17 hours GPU at 100%)
        - (15 Euro) API vastly outperforms Runpod
        - → Estimated costs: less than 350 Euro / month

**My Advice:**

Primarily use the API for LLM requests, it's easily scalable and you only pay per usage. Furthermore, LLM-API-Providers enable the use of the largest frontier models, if needed.

For 24/7 token generation and simple data processing, I would recommend a simple PC build with a single 4090 Nvidia GPU. Initial build costs are around 2,000 Euro and monthly electricity costs are negligible. This will do the job, even for processing numerous live feeds.

For an all-in approach where you want to process data for 7,000 companies or more 24/7, I would recommend a Runpod instance of an A6000 which can handle larger thinking-models and is known for its great token speed.

# Monthly Costs Estimations for Inference

- ~350 Euro or less for LLM inference
- ~3 Euro for domain → what investors see, also internal
- ~10-20 Euro for Cloud-Hosting - resource intensive n8n, many threads
    - Only ~5-10 Euro during testing phase