# Event-Driven Trading System: Project Overview

This document outlines a two-phase approach to building an algorithmic trading system based on alternative data signals. The system identifies historical correlations between specific events (e.g., FDA drug approvals, clinical trial results) and market movements, then uses those insights to trade in real-time.

---

# Phase 1: Signal Backtesting & Validation

## Objective

Quantify the historical relationship between specific alternative data signals and subsequent stock price movements. This phase establishes whether a signal has predictive power before deploying capital.

## Methodology

The approach is purely algorithmic and numerical, avoiding the complexity and overhead of training custom ML models. Event-study methodology from financial economics provides the foundation:

1. **Signal Identification**: Filter historical news sources and alternative data feeds for specific events (e.g., "medication X reached Phase III trials")
2. **Event Windowing**: For each identified event, extract the company's stock data in windows before and after the event
3. **Abnormal Returns Calculation**: Compute abnormal returns by comparing actual returns to expected returns (benchmarked against sector or market indices)
4. **CAR Analysis**: Calculate Cumulative Abnormal Returns (CAR) to measure total impact over the event window
5. **Beta Estimation**: Estimate the stock's beta to understand systematic risk exposure
6. **Signal Scoring**: Aggregate results across all historical events to derive a correlation score and confidence interval for the signal
7. **Statistical Validation**: Assess significance, consistency, and robustness of the signal across different time periods and market conditions

**Note**: Specific methodologies (e.g., event window lengths, aggregation methods, significance thresholds) will be determined empirically through testing.

## Data Requirements

### Historical Stock Price Data

- **Kaggle**: US Historical Stock Prices with Earnings Data
    - 7,000+ companies, 20 years, daily granularity
    - https://www.kaggle.com/datasets/tsaustin/us-historical-stock-prices-with-earnings-data
- **Stooq**: International Stock Market Data
    - Multiple markets, 10-30 years, daily granularity
    - https://stooq.com/t/?i=518
- **FRED**: Economic indicators and sector indices for benchmarking
    - https://fred.stlouisfed.org/

### Alternative Data Sources

- **Financial News**:
    - Kaggle: Daily Financial News for 6,000+ Stocks (2009-2020)
        - https://www.kaggle.com/datasets/miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests
    - GDELT Project: Global news events database (1979-present, updated every 15 minutes)
        - https://www.gdeltproject.org/
    - FNSPID: Financial News and Stock Price Integration Dataset (15.7M news records, 1999-2023)

- **Pharmaceutical & Biotech**:
    - ClinicalTrials.gov: 400,000+ clinical trials with phase progressions and results
        - https://clinicaltrials.gov/
    - openFDA: FDA drug approvals, rejections, safety alerts (1990s-present)
        - https://open.fda.gov/

- **Regulatory Filings**:
    - SEC EDGAR: All US public company filings (8-K for material events, 10-K/Q for earnings)
        - https://www.sec.gov/edgar
    
- **Social Sentiment** (optional):
    - Reddit archives: Retail investor sentiment (WallStreetBets, r/stocks)
    - Twitter/X: Historical financial discourse datasets

---

# Phase 2: Live Trading System

## Objective

Deploy a real-time system that monitors alternative data sources, detects validated signals, and executes trades automatically based on backtested correlations.

## System Architecture

The live system consists of five core components:

### 1. Data Ingestion Layer
- Monitor multiple alternative data sources 24/7 (news feeds, regulatory sites, pharma databases)
- Ingest and normalize data from heterogeneous sources

### 2. Signal Detection Engine
- Algorithmically filter sources for keywords and patterns matching validated signals
- Extract relevant entities (company, event type, magnitude)

### 3. Context Enhancement (Optional)
- Use an LLM-based agent to research additional context surrounding the event
- Generate a structured report with key details that may affect signal strength

### 4. Evaluation & Decision Module
- Input: Detected signal + context + historical correlation data from Phase 1
- Output: Trade recommendation with parameters:
    - Direction (long, short, neutral)
    - Instrument (equity, put, call)
    - Magnitude (position size)
    - Expected duration
    - Confidence score

**Decision Approach** (to be determined empirically):
- Option A: Pure algorithmic calculation based on signal strength and historical metrics
- Option B: LLM-based agent that interprets all inputs and makes trading decisions
- Option C: Hybrid approach with algorithmic guardrails

### 5. Execution & Risk Management
- Execute trades via broker API
- Dynamic position management: Rather than setting fixed holding periods, continuously monitor news and price action; exit positions when conditions change
- Performance tracking: Log all trades with full decision context
- Safety mechanisms:
    - Human-in-the-loop alerts via Telegram/Slack for repeated poor performance
    - Drawdown limits (specifics TBD)
    - Position size constraints (specifics TBD)

---

# Infrastructure & Costs

## Inference Options Analysis

### Option 1: API-Based LLMs
**Cost**: 3-15 Euro per million tokens (model-dependent)

**Pros**:
- No upfront hardware costs
- Easily scalable
- Access to latest frontier models (Claude, GPT-4, etc.)
- Pay only for actual usage

**Cons**:
- Recurring costs scale with usage
- Network latency
- Dependence on external providers

**Break-even**: Cheaper than dedicated GPU if usage is below ~70% utilization (17 hours/day at full load for smaller models)

### Option 2: Local GPU
**Hardware**: NVIDIA RTX 4090 (24GB VRAM)
**Cost**: ~2,000 Euro initial, ~10-20 Euro/month electricity

**Pros**:
- Low ongoing costs after initial investment
- No network latency
- Full control and privacy

**Cons**:
- Limited to smaller models
- Hardware maintenance
- Less flexibility for scaling

**Use case**: 24/7 monitoring, keyword filtering, and simple inference tasks

### Option 3: Cloud GPU
**Hardware**: Runpod RTX A6000 (48GB VRAM) or A100 (80GB VRAM)
**Cost**: 355-900 Euro/month

**Pros**:
- Run larger models
- No hardware maintenance
- Flexible scaling

**Cons**:
- High monthly costs
- Still bound by VRAM constraints

**Use case**: High-volume processing across 7,000+ companies with larger reasoning models

## Recommended Architecture

**For POC and moderate-scale deployment**:
- **Signal detection & monitoring**: Local 4090 GPU or lightweight cloud instances
- **LLM reasoning & evaluation**: API-based (Claude Sonnet, GPT-4)
- **Data storage & orchestration**: Cloud hosting (n8n or similar)

**Rationale**: APIs provide the best cost-performance for occasional high-complexity reasoning, while local/lightweight compute handles continuous monitoring efficiently.

## Cost Breakdown (Monthly Estimates)

| Component | Testing Phase | Production Phase |
|-----------|---------------|------------------|
| LLM Inference (API) | 50-100 Euro | 200-350 Euro |
| Cloud Hosting (n8n, databases) | 5-10 Euro | 10-20 Euro |
| Domain & Infrastructure | 3 Euro | 3 Euro |
| Broker API & Data Feeds | Variable | Variable |
| **Total (excluding trading capital)** | **~60-115 Euro** | **~215-375 Euro** |

**Note**: Actual costs depend heavily on trading frequency, number of monitored signals, and LLM usage patterns. These are preliminary estimates pending empirical validation.

---

# Open Questions & Next Steps

The following will be determined through empirical testing:

- Event window lengths for abnormal return calculations
- Statistical significance thresholds for signal validation
- Position sizing algorithms
- Stop-loss and take-profit strategies
- Optimal data sources for each signal type
- LLM vs. algorithmic decision-making performance
- Real-world execution costs and slippage

**Immediate next step**: Begin Phase 1 with a single well-defined signal (e.g., FDA drug approvals) to validate the backtesting methodology.