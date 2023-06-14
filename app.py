from dotenv import load_dotenv
import os
import json
import datetime
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import requests

# for graph plotting in website
# NLTK VADER for sentiment analysis
import nltk
nltk.downloader.download('vader_lexicon')

from nltk.sentiment import SentimentAnalyzer
import nltk.sentiment.util

api_url = os.getenv("API-URL")
api_key = os.getenv("API-Key")
api_host = os.getenv("RapidAPI-Host")

# logging.basicConfig(filename='app_log.log',
#                     encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True, port=8001)


def get_news_from_yahoo(ticker):

    querystring = {"symbol": "AAPL"}

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
        datatime_i = datetime.datetime.strptime(
            article['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
        date_i_str = datatime_i.strftime("%b-%d-%y")
        time_i_str = datatime_i.strftime("%I:%M%p")

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

    logging.debug(parsedata_df)

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
                 title=ticker + ' Hourly Sentiment Scores')
    return fig  # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later


def plot_daily_sentiment(parsed_and_scored_news, ticker):

    # Group by date and ticker columns from scored_news and calculate the mean
    mean_scores = parsed_and_scored_news.resample('D').mean(numeric_only=True)

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index,
                 y='sentiment_score', title=ticker + ' Daily Sentiment Scores')
    return fig  # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sentiment', methods=['POST'])
def sentiment():

    # logging.debug('In sentiment')

    ticker = request.form['ticker'].upper()

    parsed_news_df = get_news_from_yahoo(ticker)


##############################################################
    parsed_and_scored_news = score_news(parsed_news_df)
    fig_hourly = plot_hourly_sentiment(parsed_and_scored_news, ticker)
    fig_daily = plot_daily_sentiment(parsed_and_scored_news, ticker)

    graphJSON_hourly = json.dumps(
        fig_hourly, cls=PlotlyJSONEncoder)
    graphJSON_daily = json.dumps(fig_daily, cls=PlotlyJSONEncoder)

    header = "Hourly and Daily Sentiment of {} Stock".format(ticker)
    description = """
	The above chart averages the sentiment scores of {} stock hourly and daily.
	The table below gives each of the most recent headlines of the stock and the negative, neutral, positive and an aggregated sentiment score.
	The news headlines are obtained from the FinViz website.
	Sentiments are given by the nltk.sentiment.vader Python library.
    """.format(ticker)
    return render_template('sentiment.html', graphJSON_hourly=graphJSON_hourly, graphJSON_daily=graphJSON_daily, header=header, table=parsed_and_scored_news.to_html(classes='data'), description=description)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, load_dotenv=True)
