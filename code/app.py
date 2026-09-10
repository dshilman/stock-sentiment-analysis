"""Flask web app for stock news sentiment analysis.

Fetches recent news for a ticker, scores it with FinBERT, and renders
sentiment and price charts alongside a table of headlines.
"""

import json
import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
from flask import Flask, render_template, request
from plotly.utils import PlotlyJSONEncoder

from sentiment.FinbertSentiment import FinbertSentiment
from yahoo_api import API

EST = pytz.timezone("US/Eastern")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sentiment_algo = FinbertSentiment()


def get_news(ticker: str) -> pd.DataFrame:
    """Fetch news for ``ticker`` and set it as the current symbol."""
    sentiment_algo.set_symbol(ticker)
    return API.get_news(ticker)


def score_news(news_df: pd.DataFrame) -> pd.DataFrame:
    """Score the given news DataFrame and return it with sentiment columns."""
    sentiment_algo.set_data(news_df)
    sentiment_algo.calc_sentiment_score()
    return sentiment_algo.df


def plot_sentiment(ticker: str) -> go.Figure:
    """Return the sentiment bar chart for the current data."""
    return sentiment_algo.plot_sentiment()


def get_earliest_date(df: pd.DataFrame) -> pd.Timestamp:
    """Return the earliest news timestamp, localized to US/Eastern."""
    date = df["Date Time"].iloc[-1]
    py_date = date.to_pydatetime()
    return py_date.replace(tzinfo=EST)


def plot_hourly_price(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Return a line chart of the price history."""
    return px.line(
        data_frame=df, x=df["Date Time"], y="Price", title=f"{ticker} Price"
    )


def convert_headline_to_link(df: pd.DataFrame) -> pd.DataFrame:
    """Replace raw columns with a single clickable ``Headline`` column."""
    df.insert(2, "Headline", df["title + link"])
    df.drop(
        columns=["sentiment", "title + link", "title"],
        inplace=True,
        axis=1,
    )
    return df


@app.route("/", methods=["GET"])
def index():
    """Render the ticker entry form."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Run the full analysis pipeline for the submitted ticker."""
    ticker = request.form["ticker"].strip().upper()
    logger.info("Analyzing ticker: %s", ticker)

    news_df = get_news(ticker)
    if news_df.empty:
        return render_template(
            "index.html",
            error=f"No news data available for '{ticker}'.",
        )

    scored_news_df = score_news(news_df)

    fig_bar_sentiment = plot_sentiment(ticker)
    graph_sentiment = json.dumps(fig_bar_sentiment, cls=PlotlyJSONEncoder)

    earliest_datetime = get_earliest_date(news_df)
    price_history_df = get_price_history(ticker, earliest_datetime)
    fig_line_price_history = plot_hourly_price(price_history_df, ticker)
    graph_price = json.dumps(fig_line_price_history, cls=PlotlyJSONEncoder)

    scored_news_df = convert_headline_to_link(scored_news_df)

    return render_template(
        "analysis.html",
        ticker=ticker,
        graph_price=graph_price,
        graph_sentiment=graph_sentiment,
        table=scored_news_df.to_html(
            classes="mystyle", render_links=True, escape=False
        ),
    )


def get_price_history(
    ticker: str, earliest_datetime: pd.Timestamp
) -> pd.DataFrame:
    """Fetch intraday price history for ``ticker`` since ``earliest_datetime``."""
    return API.get_price_history(ticker, earliest_datetime)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True, load_dotenv=True)
