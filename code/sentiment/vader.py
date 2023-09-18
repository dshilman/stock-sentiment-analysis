import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import nltk
import nltk.sentiment.util
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from base_sentiment import SentimentAnalysisBase


class VaderSentiment (SentimentAnalysisBase):

    nltk.downloader.download('vader_lexicon')

    def __init__(self, symbol) -> None:

        self.vader = SentimentIntensityAnalyzer()
        super().__init__(symbol)

    def calc_sentiment_score(self):

        super().df['vader_sentiment'] = super().df['Headline'].apply(
            self.vader.polarity_scores)
        super().df['vader_sentiment_score'] = super(
        ).df['vader_sentiment'].apply(lambda x: x['compound'])
        super().calc_sentiment_score()

    def plot_sentiment(self) -> go.Figure:

        super().df.drop(
            super().df[super().df['vader_sentiment_score'] == 0].index, inplace=True)

        return super().plot_sentiment()
