import os
class config():
    NEWS_API_URL = "https://mboum-finance.p.rapidapi.com/v1/markets/news"
    HISTORY_API_URL = "https://mboum-finance.p.rapidapi.com/v1/markets/stock/history"
    API_Key = os.environ.get('RAPIDAPI_KEY')
    RapidAPI_Host = "mboum-finance.p.rapidapi.com"

    headers = {
        "X-RapidAPI-Key": API_Key,
        "X-RapidAPI-Host": RapidAPI_Host
    }
