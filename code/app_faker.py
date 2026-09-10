"""Flask app variant that uses fake, randomly generated data.

Useful for local development and demos without a live API key. Generates
synthetic news headlines and prices, scores them with VADER, and renders the
same charts and table as the production app.
"""

import json
import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from faker import Faker
from flask import Flask, render_template, request
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from plotly.utils import PlotlyJSONEncoder

DATE_FORMAT = "%b-%d-%y %H:%M %S"

fake = Faker()
Faker.seed(20)

app = Flask(__name__)


def get_price_history(ticker: str) -> pd.DataFrame:
    """Generate 20 days of fake daily prices."""
    start_date = datetime.now() - timedelta(days=20)

    data_rows = []
    for offset in range(20):
        date_time = start_date + timedelta(days=offset)
        price = random.randrange(100)
        data_rows.append([date_time.strftime(DATE_FORMAT), price])

    columns = ["Date Time", "Price"]
    df = pd.DataFrame(data_rows, columns=columns)
    df["Date Time"] = pd.to_datetime(df["Date Time"], format=DATE_FORMAT)
    df.sort_values(by="Date Time", ascending=True, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def get_news(ticker: str) -> pd.DataFrame:
    """Generate 20 fake news items for the last few days."""
    base_date = datetime.now() - timedelta(days=3)

    data_rows = []
    for _ in range(20):
        date_time_str = (
            base_date - timedelta(days=random.randrange(3))
        ).strftime(DATE_FORMAT)
        title = fake.paragraph(nb_sentences=1)
        description = fake.paragraph(nb_sentences=3)
        link = fake.uri()
        data_rows.append(
            [
                date_time_str,
                title,
                description,
                f'<a href="{link}">{title}</a>',
            ]
        )

    columns = ["Date Time", "Headline", "Description", "Headline + Link"]
    df = pd.DataFrame(data_rows, columns=columns)
    df["Date Time"] = pd.to_datetime(
        df["Date Time"], format=DATE_FORMAT, utc=False
    )
    df.sort_values(by="Date Time", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def score_news(news_df: pd.DataFrame) -> pd.DataFrame:
    """Score fake headlines with VADER and index by date."""
    vader = SentimentIntensityAnalyzer()
    scores = news_df["Headline"].apply(vader.polarity_scores).tolist()
    scores_df = pd.DataFrame(scores)

    scored_news_df = news_df.join(scores_df, rsuffix="_right")
    scored_news_df = scored_news_df.set_index("Date Time")
    scored_news_df = scored_news_df.rename(
        columns={"compound": "Sentiment Score"}
    )
    return scored_news_df


def plot_sentiment(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Return an hourly-max sentiment bar chart."""
    max_scores = df.resample("H").max(numeric_only=True)
    return px.bar(
        data_frame=max_scores,
        x=max_scores.index,
        y="Sentiment Score",
        title=f"{ticker} Hourly Sentiment Scores",
    )


def plot_hourly_price(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Return a line chart of the fake price history."""
    return px.line(
        data_frame=df, x=df["Date Time"], y="Price", title=f"{ticker} Price"
    )


def convert_headline_to_link(df: pd.DataFrame) -> pd.DataFrame:
    """Replace the headline column with the clickable link column."""
    df["Headline"] = df["Headline + Link"]
    df.drop("Headline + Link", inplace=True, axis=1)
    return df


@app.route("/")
def index():
    """Render the ticker entry form."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Run the full analysis pipeline using fake data."""
    ticker = request.form["ticker"].strip().upper()

    news_df = get_news(ticker)
    scored_news_df = score_news(news_df)

    fig_bar_sentiment = plot_sentiment(scored_news_df, ticker)
    graph_sentiment = json.dumps(fig_bar_sentiment, cls=PlotlyJSONEncoder)

    price_history_df = get_price_history(ticker)
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True, load_dotenv=True)
