"""Client for the Mboum Finance API (news and price history).

Provides :class:`API`, a small collection of static methods that fetch news
articles and intraday price history for a given ticker and return them as
tidy :class:`pandas.DataFrame` objects.
"""

from datetime import datetime

import pandas as pd
import pytz
import requests

from config import Config

DATE_FORMAT = "%b-%d-%y %H:%M %S"
EST = pytz.timezone("US/Eastern")
REQUEST_TIMEOUT_SECONDS = 30


class API:
    """Static client methods for the Mboum Finance endpoints."""

    @staticmethod
    def get_news(ticker: str) -> pd.DataFrame:
        """Fetch recent news articles mentioning ``ticker``.

        Args:
            ticker: The stock symbol to search for (e.g. ``"AAPL"``).

        Returns:
            A DataFrame with columns ``Date Time``, ``title``, ``Description``
            and ``title + link``. Empty if no matching articles are found.
        """
        querystring = {"symbol": ticker}

        try:
            response = requests.get(
                url=Config.NEWS_API_URL,
                headers=Config.get_headers(),
                params=querystring,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            response_json = response.json()
        except requests.RequestException as exc:
            print(f"Failed to fetch news for ticker '{ticker}': {exc}")
            return pd.DataFrame()
        except ValueError as exc:
            print(f"Invalid JSON in news response for ticker '{ticker}': {exc}")
            return pd.DataFrame()

        articles = response_json.get("body")
        if not articles:
            print(
                f"No news data returned for ticker '{ticker}', "
                f"response: {response_json}"
            )
            return pd.DataFrame()

        data_rows = []
        for article in articles:
            # Example pubDate: "Mon, 05 Jun 2023 20:46:19 +0000"
            try:
                utc_datetime = datetime.strptime(
                    article["pubDate"], "%a, %d %b %Y %H:%M:%S %z"
                )
            except (KeyError, ValueError) as exc:
                print(f"Skipping article with invalid date: {exc}")
                continue

            title = article.get("title", "")
            description = article.get("description", "")
            link = article.get("link", "")

            if ticker in title or ticker in description:
                data_rows.append(
                    [
                        utc_datetime,
                        title,
                        description,
                        f'<a href="{link}">{title}</a>',
                    ]
                )

        columns = ["Date Time", "title", "Description", "title + link"]
        df = pd.DataFrame(data_rows, columns=columns)
        if df.empty:
            return df

        df["Date Time"] = pd.to_datetime(df["Date Time"], utc=True)
        df.sort_values(by="Date Time", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def get_price_history(
        ticker: str, earliest_datetime: datetime
    ) -> pd.DataFrame:
        """Fetch intraday (5-minute) price history for ``ticker``.

        Args:
            ticker: The stock symbol to fetch prices for.
            earliest_datetime: Timezone-aware cutoff; prices before this
                moment are excluded.

        Returns:
            A DataFrame with columns ``Date Time`` and ``Price``. Empty if no
            data is returned.
        """
        querystring = {
            "symbol": ticker,
            "interval": "5m",
            "diffandsplits": "false",
        }

        try:
            response = requests.get(
                url=Config.HISTORY_API_URL,
                headers=Config.get_headers(),
                params=querystring,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            response_json = response.json()
        except requests.RequestException as exc:
            print(f"Failed to fetch price history for ticker '{ticker}': {exc}")
            return pd.DataFrame()
        except ValueError as exc:
            print(
                f"Invalid JSON in price response for ticker '{ticker}': {exc}"
            )
            return pd.DataFrame()

        price_history = response_json.get("body")
        if not price_history:
            print(
                f"No price data returned for ticker '{ticker}', "
                f"response: {response_json}"
            )
            return pd.DataFrame()

        data_rows = []
        for stock_price in price_history.values():
            date_time_num = stock_price["date_utc"]
            utc_datetime = datetime.fromtimestamp(date_time_num, tz=pytz.utc)
            est_datetime = utc_datetime.astimezone(tz=EST)

            if est_datetime < earliest_datetime:
                continue

            data_rows.append(
                [est_datetime.strftime(DATE_FORMAT), stock_price["open"]]
            )

        columns = ["Date Time", "Price"]
        df = pd.DataFrame(data_rows, columns=columns)
        if df.empty:
            return df

        df["Date Time"] = pd.to_datetime(df["Date Time"], format=DATE_FORMAT)
        df.sort_values(by="Date Time", ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
