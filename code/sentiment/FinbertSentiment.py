from transformers import pipeline
from .SentimentAnalysisBase import SentimentAnalysisBase

class FinbertSentiment (SentimentAnalysisBase):

    def __init__(self):

        self._sentiment_analysis = pipeline(
            "sentiment-analysis", model="ProsusAI/finbert")
        super().__init__()

    def calc_sentiment_score(self):

        self.df['sentiment'] = self.df['title'].apply(
            self._sentiment_analysis)
        self.df['sentiment_score'] = self.df['sentiment'].apply(
            lambda x: {x[0]['label'] == 'negative': -1, x[0]['label'] == 'positive': 1}.get(True, 0) * x[0]['score'])
