import json
import logging
import os
from datetime import datetime, timedelta

import nltk
import nltk.sentiment.util
import pandas as pd
import plotly.express as px
import pytz
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from plotly.utils import PlotlyJSONEncoder

nltk.downloader.download('vader_lexicon')


news_api_url = os.getenv("NEWS_API_URL")
history_api_url = os.getenv("HISTORY_API_URL")

api_key = os.getenv("API_Key")
api_host = os.getenv("RapidAPI-Host")

date_format = "%b-%d-%y %H:%M %S"
EST = pytz.timezone('US/Eastern')

headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": api_host
}

# logging.basicConfig(filename='app_log.log',
#                     encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)


def get_price_history(ticker, earliest_datetime):

    querystring = {"symbol": {ticker},
                   "interval": "5m", "diffandsplits": "false"}
    response = requests.get(
        history_api_url, headers=headers, params=querystring)

    respose_json = response.json()

    price_history = respose_json['items']
    data_dict = []

    print(f"earliest_datetime: {earliest_datetime}")
    for stock_price in price_history.values():

        date_time_num = stock_price["date_utc"]
        utc_datetime = datetime.fromtimestamp(date_time_num, tz=pytz.utc)
        est_datetime = utc_datetime.astimezone(tz=EST)

        if est_datetime < earliest_datetime:
            continue

        price = stock_price["open"]
        data_dict.append([est_datetime.strftime(date_format), price])

    # Set column names
    columns = ['Date Time', 'Price']
    df = pd.DataFrame(data_dict, columns=columns)
    df['Date Time'] = pd.to_datetime(df['Date Time'], format=date_format)
    df.sort_values(by='Date Time', ascending=True)
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)

    return df


def get_news(ticker):

    querystring = {"symbol": ticker}

    response = requests.get(news_api_url, headers=headers, params=querystring)

    respose_json = response.json()
    data_dict = []

    if 'item' in respose_json:
        articles = respose_json['item']
        for article in articles:
            # Mon, 05 Jun 2023 20:46:19 +0000
            utc_datetime = datetime.strptime(
                article['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
            est_datetime = utc_datetime.astimezone(tz=EST)

            date_time_i_str = est_datetime.strftime(date_format)
            title_i = article['title']
            description_i = article['description']
            link_i = article['link']
            data_dict.append([date_time_i_str, title_i, description_i, [title_i, link_i]])

        # Set column names
        columns = ['Date Time', 'Headline', 'Description', 'Placeholder']
        df = pd.DataFrame(data_dict, columns=columns)
        df['Date Time'] = pd.to_datetime(
            df['Date Time'], format=date_format, utc=False)

        df.sort_values(by='Date Time', ascending=False)
        df.reset_index(inplace=True)
        df.drop('index', axis=1, inplace=True)
    else:
        print (f"no news feed for {ticker}")
        raise Exception(f"no news feed for {ticker}")
   
    return df


def get_earliest_date(df):

    date = df['Date Time'].iloc[-1]
    py_date = date.to_pydatetime()
    return py_date.replace(tzinfo=EST)


def score_news(news_df):
    vader = SentimentIntensityAnalyzer()
    scores = news_df['Headline'].apply(vader.polarity_scores).tolist()
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    scored_news_df = news_df.join(scores_df, rsuffix='_right')
    scored_news_df = scored_news_df.set_index('Date Time')
    scored_news_df = scored_news_df.rename(
        columns={"compound": "Sentiment Score"})

    return scored_news_df


def plot_sentiment(df, ticker):

    # Group by date and ticker columns from scored_news and calculate the max
    max_scores = df.resample('H').max(numeric_only=True)

    # Plot a bar chart with plotly
    fig = px.bar(max_scores, x=max_scores.index, y='Sentiment Score',
                 title=f"{ticker} Hourly Sentiment Scores")
    return fig


def plot_hourly_price(df, ticker):

    fig = px.line(data_frame=df, x=df['Date Time'],
                  y="Price", title=f"{ticker} Price")
    return fig


app = Flask(__name__)


@app.route('/')
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

    # 7. render output
    # scored_news_df['Headline'] = scored_news_df['Headline'].apply(lambda title: f'<a href="{title[1]}">{title[0]}</a>')
    
    scored_news_df = make_prety(scored_news_df)
    return render_template('analysis.html', ticker=ticker, graph_price=graph_price, graph_sentiment=graph_sentiment, table=scored_news_df.to_html(classes='mystyle'))

def style_negative(v, props=''):
    return props if v < 0.5 else None

def make_prety(df):

    # df['Headline'] = df['Headline'].apply(lambda title: f'<a href="{title[1]}">{title[0]}</a>')
    
    df['Headline'] = df['Placeholder']
    df.style.format({'Headline': get_link})
    df.drop('Placeholder', inplace=True, axis=1)
  
    df = df.style.applymap(style_negative, props='color:red;').applymap(lambda v: 'opacity: 20%;' if (v > 0.5) else None)
    props = 'font-family: "color: #e83e8c; font-size:1.3em;'
    df = df.style.set_table_styles([{'selector': 'td.col1', 'props': props}])

    return df

def get_link(value):
    return f'<a href="{value[1]}">{value[0]}</a>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, load_dotenv=True)
