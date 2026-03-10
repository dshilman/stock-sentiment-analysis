
# Stock Sentiment Analysis — Code, Architecture, and Deployment Guide

> GitHub: https://github.com/dshilman/stock-sentiment-analysis  
> Demo video: https://www.youtube.com/watch?v=tmqi-GApZEU

## TL;DR
A Python/Flask web app that pulls a stock’s **news** and **price history** from the Mboum Finance API, scores the news using an NLP sentiment model, and renders **interactive Plotly charts** plus a clickable headlines table. The core request path is: submit ticker → call `/analyze` → fetch news → score sentiment → fetch price history (from the earliest news date) → render charts + table. citeturn1search6

---

## 1) Application Purpose
This app explores a practical fintech idea: **make news more actionable for traders** by correlating **news sentiment** with **stock price performance**. Traders can quickly gauge whether recent coverage is positive/negative and compare it with price moves over the same window. (See _Implementation_ outline and visuals in the repo README.) citeturn1search1

---

## 2) High‑Level Architecture
**Front end** (Jinja2 templates + Tailwind CDN) sends a ticker to Flask → **Flask** orchestrates the workflow → **Data layer** (Mboum API via RapidAPI) returns news and price history → **Sentiment layer** (transformers/VADER) computes scores → **Visualization** (Plotly) builds interactive charts → results rendered in `analysis.html` with links for headlines. citeturn1search5turn1search6turn1search27turn1search29turn1search30

### Request flow (happy path)
1. **GET /** → render `index.html` (ticker form). citeturn1search6turn1search5
2. **POST /analyze** → 
   - Fetch news for ticker → `API.get_news()`
   - Score news → `FinbertSentiment` (transformers) → `sentiment_score`
   - Compute earliest news timestamp → filter price history request window
   - Fetch price history → `API.get_price_history()`
   - Build Plotly figures (bar for sentiment, line for price)
   - Insert clickable headline links and render `analysis.html`. citeturn1search6turn1search27turn1search28

> **Notes**
> * The base class handles filtering neutral scores (0) from the sentiment bar chart. citeturn1search29
> * A VADER implementation is also available as an alternative sentiment engine. citeturn1search30

---

## 3) Repository Layout
A concise view of key files/folders you’ll touch most:

```
stock-sentiment-analysis/
├─ .github/workflows/            # CI workflows (folder exists in repo)
├─ code/
│  ├─ app.py                     # Flask app: routes + orchestration
│  ├─ app_faker.py               # Offline/demo app using Faker + VADER
│  ├─ config.py                  # Mboum endpoints + headers (RapidAPI)
│  ├─ yahoo_api.py               # HTTP client for news & price history
│  ├─ linux.sh                   # Convenience setup/run script (Linux)
│  ├─ templates/
│  │  ├─ index.html              # Ticker form (Tailwind via CDN)
│  │  └─ analysis.html           # Charts + clickable headlines table
│  ├─ sentiment/
│  │  ├─ SentimentAnalysisBase.py
│  │  ├─ FinbertSentiment.py     # transformers-based sentiment
│  │  └─ VaderSentiment.py       # NLTK VADER alternative
│  └─ static/                    # (placeholder for static assets)
├─ requirements.txt              # Python dependencies
└─ README.md                     # Project overview & screenshots
```
(See file tree and individual files in the repository.) citeturn1search1turn1search25turn1search6turn1search5turn1search25turn1search26turn1search27turn1search33turn1search29turn1search28turn1search30

---

## 4) Core Modules & How They Work

### 4.1 Flask App (`code/app.py`)
- Defines routes `GET /` and `POST /analyze`.
- Calls helpers to fetch **news** and **prices**, compute **sentiment**, and build **Plotly** figures.
- Converts the **Headline** column into **clickable links** before rendering. citeturn1search6

### 4.2 API Client (`code/yahoo_api.py`) & Config (`code/config.py`)
- **Endpoints** (RapidAPI host):
  - News: `https://mboum-finance.p.rapidapi.com/v1/markets/news`
  - Price History: `https://mboum-finance.p.rapidapi.com/v1/markets/stock/history`
- Uses headers with `X-RapidAPI-Key` from the `RAPIDAPI_KEY` **environment variable**.
- `get_news(ticker)`: parses Mboum’s JSON, filters for the ticker, normalizes into a DataFrame with a `title + link` column for rendering.
- `get_price_history(ticker, earliest_datetime)`: fetches 5‑minute interval data, converts timestamps to **US/Eastern**, and returns a two‑column DataFrame (`Date Time`, `Price`). citeturn1search26turn1search27

> For general Mboum Finance API docs and RapidAPI listing, see the official documentation. citeturn1search13turn1search14

### 4.3 Sentiment Engines (`code/sentiment/*`)
- **Base class**: holds common wiring and renders a bar chart of `sentiment_score` over time, excluding neutral (0) entries. citeturn1search29
- **FinbertSentiment**: uses a Hugging Face **transformers** pipeline; maps labels to numeric scores: *positive → +1*, *negative → −1*, *neutral → 0*, weighted by model confidence. citeturn1search28
- **VaderSentiment**: uses **NLTK VADER**; the `compound` polarity becomes `sentiment_score`. citeturn1search30

### 4.4 Templates & Visualization
- `index.html` provides a minimal Tailwind‑styled form that POSTs to `/analyze`.
- `analysis.html` renders the **line chart** for price, the **bar chart** for sentiment, and an **HTML table** with clickable headlines. citeturn1search5turn1search25

---

## 5) Data Sources
- **News** and **price history** are fetched from **Mboum Finance API** via RapidAPI. This repo uses the `v1/markets/news` and `v1/markets/stock/history` endpoints and expects a valid `RAPIDAPI_KEY`. citeturn1search26  
- Mboum documentation and RapidAPI product page provide broader endpoint coverage and authentication details. citeturn1search13turn1search14

---

## 6) Running the App Locally

### 6.1 Prerequisites
- **Python 3.9+** (tested on Linux/macOS)
- A **RapidAPI key** for Mboum set as env var: `RAPIDAPI_KEY`

### 6.2 Install & Run
From the project root:

```bash
# 1) install deps
python3 -m pip install -r requirements.txt

# 2) export your RapidAPI key
export RAPIDAPI_KEY="<your-rapidapi-key>"

# 3) start the Flask app
cd code
python3 app.py
```
By default the server binds `0.0.0.0` on port **81** (see `app.py`). Open your browser to `http://localhost:81/`. citeturn1search6

> **One‑liner on Linux (as used in `linux.sh`)**
> ```bash
> #!/bin/sh
> sudo wget https://bootstrap.pypa.io/get-pip.py && sudo python3 ./get-pip.py
> sudo dnf install -y cronie cronie-anacron
> cd stock-sentiment-analysis
> sudo TMPDIR=~/tmp/ python3 -m pip install -r requirements.txt --no-cache-dir
> cd code && sudo python3 app.py
> ```
> This is exactly what the repo’s `code/linux.sh` script automates. citeturn1search33

### 6.3 Offline Demo (no API key)
If you want to try the UI without calling external APIs, run the **faker‑driven** version:

```bash
cd code
python3 app_faker.py
```
It seeds fake headlines/prices and uses VADER for sentiment to render the same charts/templates. citeturn1search34

---

## 7) Deployment Options

### Option A — Simple EC2/VM (script‑based)
1. Provision a small Linux host (e.g., Amazon Linux/Fedora) and clone the repo.
2. Set `RAPIDAPI_KEY` in the environment (e.g., in `/etc/environment`).
3. Run the included `code/linux.sh` to install pip, dependencies, and start the app. Consider running under a process manager (systemd) and serving behind Nginx for TLS. citeturn1search33

### Option B — Containerize (suggested enhancement)
- Create a lightweight Dockerfile, mount `RAPIDAPI_KEY` as a secret, expose port **81**, and deploy to your container platform of choice (ECS/Fargate, Azure Web Apps for Containers, etc.). *(This repo doesn’t ship a Dockerfile by default; this is a recommended improvement.)*

---

## 8) Configuration & Environment
- **Secrets**: never commit your API keys. The app reads `RAPIDAPI_KEY` from the environment during runtime. citeturn1search26
- **Time zone**: price history timestamps are converted to **US/Eastern** for alignment with news; earliest news time defines the price history window. citeturn1search6turn1search27

---

## 9) Tech Stack
- **Backend**: Python, **Flask**. citeturn1search6  
- **NLP**: Hugging Face **transformers** (FinBERT‑style) and **NLTK VADER**. citeturn1search28turn1search30  
- **Data/HTTP**: `requests`, **pandas**. citeturn1search27  
- **Viz**: **Plotly** (Express + Graph Objects, serialized via `PlotlyJSONEncoder`). citeturn1search6  
- **UI**: Jinja2 templates + Tailwind CDN. citeturn1search5

> Exact versions are pinned in `requirements.txt` (install via pip). citeturn1search31

---

## 10) Troubleshooting
- **401/403 from Mboum** → ensure `RAPIDAPI_KEY` is set and valid; check RapidAPI quota. citeturn1search14
- **Empty charts** → no recent articles matched the ticker filter; try a more active ticker. citeturn1search27
- **Port already in use** → change the `port` in `app.run(...)` or stop the conflicting service. citeturn1search6

---

## 11) Acknowledgments
- **Mboum Finance API** for market data and news. citeturn1search13turn1search14
- **Hugging Face transformers / FinBERT** and **NLTK VADER** for sentiment models. citeturn1search28turn1search30

---

## 12) Appendix — How the Sentiment Score Is Calculated
- **FinbertSentiment**: applies a transformers pipeline to each title and translates labels to numeric scores (`+1/-1/0`) weighted by confidence. citeturn1search28
- **VADER**: uses `compound` polarity in the `[-1, 1]` range as `sentiment_score`. citeturn1search30

