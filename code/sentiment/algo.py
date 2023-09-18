from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from transformers import pipeline

class SentimentAnalysisBase():

    def __init__(self):
        pass
    
    def set_symbol(self, symbol): 
        self.symbol = symbol

    def set_data(self, df):

        self.df = df

    def calc_sentiment_score(self):
        pass

    def get_sentiment_scores(self):
        return self.df

    def plot_sentiment(self) -> go.Figure:

        column = 'sentiment_score'

        df_plot = self.df.drop(
            self.df[self.df[f'{column}'] == 0].index)

        fig = px.bar(data_frame=df_plot, x=df_plot['Date Time'], y=f'{column}',
                     title=f"{self.symbol} Hourly Sentiment Scores")
        return fig


class FinbertSentiment (SentimentAnalysisBase):

    def __init__(self):

        self._sentiment_analysis = pipeline(
            "sentiment-analysis", model="ProsusAI/finbert")
        super().__init__()

    def calc_sentiment_score(self):

        self.df['sentiment'] = self.df['Headline'].apply(
            self._sentiment_analysis)
        self.df['sentiment_score'] = self.df['sentiment'].apply(
            lambda x: {x[0]['label'] == 'negative': -1, x[0]['label'] == 'positive': 1}.get(True, 0) * x[0]['score'])
        super().calc_sentiment_score()

    def plot_sentiment(self) -> go.Figure:

        return super().plot_sentiment()
