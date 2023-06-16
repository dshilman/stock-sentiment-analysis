import json
import logging
import os
from datetime import datetime, timedelta

import nltk
import nltk.sentiment.util
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# logging.basicConfig(filename='app_log.log',
#                     encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True, port=8001)


def convert_to_est_datetime(data_time_num):

    utc_datetime = datetime.fromtimestamp(data_time_num, tz=pytz.utc)
    est_datetime = utc_datetime.astimezone(
        pytz.timezone('US/Eastern')).strftime("%b-%d-%y %I:%M%p")

    return est_datetime


def get_price_history_from_yahoo(ticker):

    querystring = {"symbol": {ticker},
                   "interval": "15m", "diffandsplits": "false"}
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
        est_date_time = convert_to_est_datetime(date_time_num)
        price = stock_price["open"]
        data_dict.append([est_date_time, price])


    # Set column names
    columns = ['datetime', 'price']
    df = pd.DataFrame(data_dict, columns=columns)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = filter_by_date(df)
    df.sort_values(by='datetime', ascending=False)
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)

    return df

def filter_by_date(df):

    today = datetime.today()
    day = timedelta(days = 1)
    yesterday = today - day

    df = df[df['datetime'].dt.date > yesterday.date]

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
        datatime_i_utc = datetime.strptime(
            article['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
        est_datetime = datatime_i_utc.astimezone(pytz.timezone('US/Eastern'))
        date_i_str = est_datetime.strftime("%b-%d-%y")
        time_i_str = est_datetime.strftime("%I:%M%p")

        # date_time_i_str = datatime_i.strftime("%Y-%m-%d %H:%M:%S")
        title_i = article['title']
        data_dict.append([date_i_str, time_i_str, title_i])

    # Set column names
    columns = ['date', 'time', 'headline']
    parsedata_df = pd.DataFrame(data_dict, columns=columns)
    parsedata_df['datetime'] = pd.to_datetime(
        parsedata_df['date'] + ' ' + parsedata_df['time'])

    parsedata_df.sort_values(by='datetime', ascending=False)
    parsedata_df.reset_index(inplace=True)
    parsedata_df.drop('index', axis=1, inplace=True)

    return parsedata_df


def score_news(parsed_news_df):
    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()

    # Iterate through the headlines and get the polarity scores using vader
    scores = parsed_news_df['headline'].apply(vader.polarity_scores).tolist()

    # Convert the 'scores' list of dicts into a DataFrame
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    parsed_and_scored_news = parsed_news_df.join(scores_df, rsuffix='_right')

    parsed_and_scored_news = parsed_and_scored_news.set_index('datetime')

    parsed_and_scored_news = parsed_and_scored_news.drop(
        ['date', 'time'], axis=1)

    parsed_and_scored_news = parsed_and_scored_news.rename(
        columns={"compound": "sentiment_score"})

    return parsed_and_scored_news


def plot_hourly_sentiment(parsed_and_scored_news, ticker):

    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('H').mean(numeric_only=True)

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score',
                 title=f"{ticker} Hourly Sentiment Scores")
    return fig  # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later


def plot_daily_sentiment(parsed_and_scored_news, ticker):

    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('D').mean(numeric_only=True)

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index,
                 y='sentiment_score', title=f"{ticker} Daily Sentiment Scores")
    return fig  # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later


def plot_hourly_price(df, ticker):

    print(df)
    fig = go.Figure([go.Scatter(x=df['datetime'], y=df['price'],
                    title=f"{ticker} Daily Stock Price Performance")])
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
    fig_daily = plot_daily_sentiment(scored_news, ticker)

######################################################################

    price_history_df = get_price_history_from_yahoo(ticker)
    fig_price_history = plot_hourly_price(price_history_df, ticker)

    graphJSON_hourly = json.dumps(fig_hourly, cls=PlotlyJSONEncoder)
    graphJSON_daily = json.dumps(fig_daily, cls=PlotlyJSONEncoder)
    graphJSON_price = json.dumps(fig_price_history, cls=PlotlyJSONEncoder)

    return render_template('sentiment.html', ticker=ticker, graphJSON_price=graphJSON_price, graphJSON_hourly=graphJSON_hourly, graphJSON_daily=graphJSON_daily, table=scored_news.to_html(classes='data'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, load_dotenv=True)
