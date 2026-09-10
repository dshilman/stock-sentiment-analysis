"""VADER-based sentiment analysis."""

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from .SentimentAnalysisBase import SentimentAnalysisBase


class VaderSentiment(SentimentAnalysisBase):
    """Sentiment scoring using NLTK's VADER analyzer."""

    def __init__(self) -> None:
        nltk.download("vader_lexicon", quiet=True)
        self.vader = SentimentIntensityAnalyzer()
        super().__init__()

    def calc_sentiment_score(self) -> None:
        """Score each title and store the compound score in ``sentiment_score``."""
        self.df["sentiment"] = self.df["title"].apply(
            self.vader.polarity_scores
        )
        self.df["sentiment_score"] = self.df["sentiment"].apply(
            lambda scores: scores["compound"]
        )
