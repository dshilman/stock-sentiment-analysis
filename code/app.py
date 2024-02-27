import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
from flask import Flask, render_template, request
from plotly.utils import PlotlyJSONEncoder

from sentiment.FinbertSentiment import FinbertSentiment
from yahoo_api import API

EST = pytz.timezone('US/Eastern')

# logging.basicConfig(filename='app_log.log',
#                     encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)

def get_price_history(ticker: str, earliest_datetime: pd.Timestamp) -> pd.DataFrame:

    return API.get_price_history(ticker, earliest_datetime)
    

sentimentAlgo = FinbertSentiment()

def get_news(ticker) -> pd.DataFrame:

    sentimentAlgo.set_symbol(ticker)

    return API.get_news(ticker)


def score_news(news_df: pd.DataFrame) -> pd.DataFrame:

    sentimentAlgo.set_data(news_df)
    sentimentAlgo.calc_sentiment_score()

    return sentimentAlgo.df


def plot_sentiment(df: pd.DataFrame, ticker: str) -> go.Figure:

    return sentimentAlgo.plot_sentiment()


def get_earliest_date(df: pd.DataFrame) -> pd.Timestamp:

    date = df['Date Time'].iloc[-1]
    py_date = date.to_pydatetime()
    return py_date.replace(tzinfo=EST)


def plot_hourly_price(df, ticker) -> go.Figure:

    fig = px.line(data_frame=df, x=df['Date Time'],
                  y="Price", title=f"{ticker} Price")
    return fig


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():

    ticker = request.form['ticker'].strip().upper()
    # 1. get news feed
    news_df = get_news(ticker)
    # 2. calculate sentiment scores
    scored_news_df = score_news(news_df)
    # 3. create a bar diagram
    fig_bar_sentiment = plot_sentiment(scored_news_df, ticker)
    graph_sentiment = json.dumps(fig_bar_sentiment, cls=PlotlyJSONEncoder)
    # 4. get earliest data time from the news data feed
    earliest_datetime = get_earliest_date(news_df)
    # 5. get price history for the ticker, ignore price history earlier than the news feed
    price_history_df = get_price_history(ticker, earliest_datetime)
    # 6. create a linear diagram
    fig_line_price_history = plot_hourly_price(price_history_df, ticker)
    graph_price = json.dumps(fig_line_price_history, cls=PlotlyJSONEncoder)
    # 7. Make the Headline column clickable
    # scored_news_df['Headline'] = scored_news_df['Headline'].apply(lambda title: f'<a href="{title[1]}">{title[0]}</a>')
    scored_news_df = convert_headline_to_link(scored_news_df)

    # 8. render output
    return render_template('analysis.html', ticker=ticker, graph_price=graph_price, graph_sentiment=graph_sentiment, table=scored_news_df.to_html(classes='mystyle', render_links=True, escape=False))


def convert_headline_to_link(df: pd.DataFrame) -> pd.DataFrame:

    df['Headline'] = df['title + link']
    df.drop(columns = ['sentiment', 'title + link'], inplace=True, axis=1)

    return df


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True, load_dotenv=True)

