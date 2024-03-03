from datetime import datetime
import pandas as pd
import requests
from config import config
import pandas as pd
import pytz

date_format = "%b-%d-%y %H:%M %S"
EST = pytz.timezone('US/Eastern')
class API():
    def __init__(self) -> None:
        pass

    def get_news(ticker):
        date_format = "%b-%d-%y %H:%M %S"

        querystring = {"symbol": f"{ticker}"}

        response = requests.get(
            url=config.NEWS_API_URL, headers=config.headers, params=querystring)

        respose_json = response.json()
        # print(respose_json)
        data_array = []

        if 'body' in respose_json:
            articles = respose_json['body']
            for article in articles:
                # Mon, 05 Jun 2023 20:46:19 +0000
                utc_datetime = datetime.strptime(
                    article['pubDate'], '%a, %d %b %Y %H:%M:%S %z')

                title_i = article['title']
                description_i = article['description']
                link_i = article['link']
                # Set column names
                if ticker in title_i or ticker in description_i:
                    data_array.append(
                        [utc_datetime, title_i, description_i, f'<a href="{link_i}">{title_i}</a>'])

            # Set column names
            columns = ['Date Time', 'title',
                       'Description', 'title + link']

            df = pd.DataFrame(data_array, columns=columns)
            df['Date Time'] = pd.to_datetime(
                df['Date Time'], format=date_format, utc=True)
            df.set_index('Date Time', inplace=True)
            df.sort_values(by='Date Time', ascending=False)
            df.reset_index(inplace=True)
        else:
            print(f'No data returned for ticker: {ticker}, response: {respose_json}')
            df = pd.DataFrame()

        return df

    def get_price_history(ticker: str, earliest_datetime: pd.Timestamp) -> pd.DataFrame:

        querystring = {"symbol": {ticker},
                    "interval": "5m", "diffandsplits": "false"}
        
        response = requests.get(url=config.HISTORY_API_URL, headers=config.headers, params=querystring)

        respose_json = response.json()

        price_history = respose_json['body']
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
