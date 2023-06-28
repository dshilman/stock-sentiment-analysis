import json
import logging
from datetime import datetime, timedelta
from faker import Faker
from faker.providers import date_time
from faker.providers import internet
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import pytz
from dotenv import load_dotenv
from flask import Flask, render_template, request
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from plotly.utils import PlotlyJSONEncoder


fake = Faker()
Faker.seed(20)

date_format = "%b-%d-%y %H:%M %S"
EST = pytz.timezone('US/Eastern')


app = Flask(__name__)


def get_price_history(ticker):

    data_dict = []

    date = datetime.now() - timedelta(days=20)

    for i in range(20):

        date_time_num = date + timedelta(days=i)
        price = random.randrange(100)
        data_dict.append([date_time_num.strftime(date_format), price])

    # Set column names
    columns = ['Date Time', 'Price']
    df = pd.DataFrame(data_dict, columns=columns)
    df['Date Time'] = pd.to_datetime(df['Date Time'], format=date_format)
    df.sort_values(by='Date Time', ascending=True)
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)

    return df


def get_news(ticker) -> pd.DataFrame:

    date = datetime.now() - timedelta(days=3)

    data_dict = []
    for i in range(20):
        # Mon, 05 Jun 2023 20:46:19 +0000

        date_time_i_str = (
            date - timedelta(days=random.randrange(3))).strftime(date_format)
        title_i = fake.paragraph(nb_sentences=1)
        description_i = fake.paragraph(nb_sentences=3)
        link_i = fake.uri()
        data_dict.append(
            [date_time_i_str, title_i, description_i, f'<a href="{link_i}">{title_i}</a>'])

    # Set column names
    columns = ['Date Time', 'Headline', 'Description', 'Headline + Link']
    df = pd.DataFrame(data_dict, columns=columns)
    df['Date Time'] = pd.to_datetime(
        df['Date Time'], format=date_format, utc=False)

    df.sort_values(by='Date Time', ascending=False)
    df.reset_index(inplace=True)
    df.drop('index', axis=1, inplace=True)

    return df


def score_news(news_df) -> pd.DataFrame:
    vader = SentimentIntensityAnalyzer()
    scores = news_df['Headline'].apply(vader.polarity_scores).tolist()
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    scored_news_df = news_df.join(scores_df, rsuffix='_right')
    scored_news_df = scored_news_df.set_index('Date Time')
    scored_news_df = scored_news_df.rename(
        columns={"compound": "Sentiment Score"})

    return scored_news_df

def plot_sentiment(df, ticker) -> go.Figure:

    # Group by date and ticker columns from scored_news and calculate the max
    max_scores = df.resample('H').max(numeric_only=True)

    # Plot a bar chart with plotly
    fig = px.bar(data_frame=max_scores, x=max_scores.index, y='Sentiment Score',
                 title=f"{ticker} Hourly Sentiment Scores")
    return fig


def plot_hourly_price(df, ticker) -> go.Figure:

    fig = px.line(data_frame=df, x=df['Date Time'],
                  y="Price", title=f"{ticker} Price")
    return fig


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
    # 5. get price history for the ticker, ignore price history earlier than the news feed
    price_history_df = get_price_history(ticker)
    # 6. create a linear diagram
    fig_line_price_history = plot_hourly_price(price_history_df, ticker)
    graph_price = json.dumps(fig_line_price_history, cls=PlotlyJSONEncoder)
    # 7. Make the Headline column clickable
    # scored_news_df['Headline'] = scored_news_df['Headline'].apply(lambda title: f'<a href="{title[1]}">{title[0]}</a>')
    scored_news_df = convert_headline_to_link(scored_news_df)

    # 8. render output
    return render_template('analysis.html', ticker=ticker, graph_price=graph_price, graph_sentiment=graph_sentiment, table=scored_news_df.to_html(classes='mystyle', render_links=True, escape=False))


def convert_headline_to_link(df: pd.DataFrame) -> pd.DataFrame:

    # df['Headline'] = df['Headline'].apply(lambda title: f'<a href="{title[1]}">{title[0]}</a>')

    df['Headline'] = df['Headline + Link']
    df.drop('Headline + Link', inplace=True, axis=1)

    return df


def style_negative(v, props=''):
    return props if float(v) < 0.5000 else None


def style_positive(v, props=''):
    return props if float(v) > 0.5000 else None

    # df.style.applymap(func=style_negative, props='color:red;', subset=['Sentiment Score'])\
    #     .applymap(func=style_positive, props= 'opacity: 20%;', subset=['Sentiment Score'])

    # # df.style.set_table_styles(table_styles=[
    #         {'selector': "td.col1",
    #          'props': 'font-family, color: #e83e8c; font-size:1.3em;'}
    #     ])\
    #     .format(escape="html")\
    #     .background_gradient(axis=None, vmin=1, vmax=5, cmap="YlGnBu")\
    #     .set_sticky(axis="index")

    return df


# def get_link(value):
#     return f'<a href="{value[1]}">{value[0]}</a>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, load_dotenv=True)
