from datetime import datetime
import pandas as pd
import requests
from config import config
import pandas as pd


class API():
    def __init__(self) -> None:
        pass

    def get_news(self, ticker):
        date_format = "%b-%d-%y %H:%M %S"

        querystring = {"symbol": f"{ticker}"}

        response = requests.get(
            url=config.NEWS_API_URL, headers=config.headers, params=querystring)

        respose_json = response.json()

        data_array = []

        if 'item' in respose_json:
            articles = respose_json['item']
            for article in articles:
                # Mon, 05 Jun 2023 20:46:19 +0000
                utc_datetime = datetime.strptime(
                    article['pubDate'], '%a, %d %b %Y %H:%M:%S %z')

                title_i = article['title']
                description_i = article['description']
                link_i = article['link']
                # Set column names
                data_array.append(
                    [utc_datetime, title_i, description_i, f'<a href="{link_i}">{title_i}</a>'])

            # Set column names
            columns = ['Date Time', 'Headline',
                       'Description', 'Headline + Link']

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
