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


api_url = os.getenv("API_URL")
api_key = os.getenv("API_Key")
api_host = os.getenv("RapidAPI-Host")

date_format = "%b-%d-%y %I:%M %p"
EST = pytz.timezone('US/Eastern')


# logging.basicConfig(filename='app_log.log',
#                     encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)


# def convert_to_est_datetime(date_time_num):

#     utc_datetime = datetime.fromtimestamp(date_time_num, tz=pytz.utc)
#     est_datetime = utc_datetime.astimezone(tz=EST)

#     return est_datetime


def get_price_history_from_yahoo(ticker, earliest_datetime):

    querystring = {"symbol": {ticker},
                   "interval": "5m", "diffandsplits": "false"}
    url_price = "https://mboum-finance.p.rapidapi.com/hi/history"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }

    response = requests.get(url_price, headers=headers, params=querystring)

    # with open(file='sample.json', mode='r', encoding="utf8") as myfile:
    #     data = myfile.read()

    respose_json = response.json()

    price_history = respose_json['items']
    data_dict = []

    for stock_price in price_history.values():

        date_time_num = stock_price["date_utc"]
        # est_date_time = convert_to_est_datetime(date_time_num)
        utc_datetime = datetime.fromtimestamp(date_time_num, tz=pytz.utc)
        est_datetime = utc_datetime.astimezone(tz=EST)

        # today = datetime.now(tz=EST)
        # three_days = timedelta(days=1)
        # not_before_date = today - three_days

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


def get_news_from_yahoo(ticker):

    querystring = {"symbol": ticker}

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }

    response = requests.get(api_url, headers=headers, params=querystring)

    # with open(file='sample.json', mode='r', encoding="utf8") as myfile:
    #     data = myfile.read()

    respose_json = response.json()

    articles = respose_json['item']
    data_dict = []

    for article in articles:
        # Mon, 05 Jun 2023 20:46:19 +0000
        utc_datetime = datetime.strptime(
            article['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
        est_datetime = utc_datetime.astimezone(tz=EST)

        # date_i_str = est_datetime.strftime("%b-%d-%y")
        # time_i_str = est_datetime.strftime("%I:%M%p")

        date_time_i_str = est_datetime.strftime(date_format)
        title_i = article['title']
        description_i = article['description']
        data_dict.append([date_time_i_str, title_i, description_i])

    # Set column names
    columns = ['Date Time', 'Headline', 'Description']
    parsedata_df = pd.DataFrame(data_dict, columns=columns)
    parsedata_df['Date Time'] = pd.to_datetime(
        parsedata_df['Date Time'], format=date_format, utc=False)

    parsedata_df.sort_values(by='Date Time', ascending=False)
    parsedata_df.reset_index(inplace=True)
    parsedata_df.drop('index', axis=1, inplace=True)

    return parsedata_df

def get_earliest_date(df):

    date = df['Date Time'].iloc[-1]    
    py_date =  date.to_pydatetime()
    return py_date.replace(tzinfo=EST)


def score_news(news_df):
    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()

    # Iterate through the headlines and get the polarity scores using vader
    scores = news_df['Description'].apply(vader.polarity_scores).tolist()

    # Convert the 'scores' list of dicts into a DataFrame
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    scored_news_df = news_df.join(scores_df, rsuffix='_right')
    scored_news_df = scored_news_df.set_index('Date Time')
    scored_news_df = scored_news_df.rename(
        columns={"compound": "Sentiment Score"})

    return scored_news_df


def plot_hourly_sentiment(df, ticker):

    # Group by date and ticker columns from scored_news and calculate the mean
    max_scores = df.resample('H').max(numeric_only=True)

    # Plot a bar chart with plotly
    fig = px.bar(max_scores, x=max_scores.index, y='Sentiment Score',
                 title=f"{ticker} Hourly Sentiment Scores")
    return fig


def plot_hourly_price(df, ticker):

    fig = px.line(data_frame=df, x=df['Date Time'], y="Price", title=f"{ticker} Price")
    return fig


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sentiment', methods=['POST'])
def sentiment():

    # logging.debug('In sentiment')

    ticker = request.form['ticker'].upper()
    news_df = get_news_from_yahoo(ticker)


##############################################################
    scored_news = score_news(news_df)
    fig_hourly = plot_hourly_sentiment(scored_news, ticker)

    earliest_datetime = get_earliest_date(news_df)
    price_history_df = get_price_history_from_yahoo(ticker, earliest_datetime)
    fig_price_history = plot_hourly_price(price_history_df, ticker)

######################################################################

    graph_sentiment = json.dumps(fig_hourly, cls=PlotlyJSONEncoder)
    graph_price = json.dumps(fig_price_history, cls=PlotlyJSONEncoder)

    return render_template('sentiment.html', ticker=ticker, graph_price=graph_price, graph_sentiment=graph_sentiment, table=scored_news.to_html())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, load_dotenv=True)
