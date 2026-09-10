"""FinBERT-based sentiment analysis."""

from transformers import pipeline

from .SentimentAnalysisBase import SentimentAnalysisBase


class FinbertSentiment(SentimentAnalysisBase):
    """Sentiment scoring using the ProsusAI/finbert model."""

    def __init__(self) -> None:
        self._sentiment_analysis = pipeline(
            "sentiment-analysis", model="ProsusAI/finbert"
        )
        super().__init__()

    def calc_sentiment_score(self) -> None:
        """Score each title and store a signed score in ``sentiment_score``.

        The score is positive for ``positive`` labels, negative for
        ``negative`` labels, and zero otherwise, scaled by the model's
        confidence.
        """
        self.df["sentiment"] = self.df["title"].apply(self._sentiment_analysis)
        self.df["sentiment_score"] = self.df["sentiment"].apply(
            self._signed_score
        )

    @staticmethod
    def _signed_score(sentiment: list) -> float:
        """Convert a FinBERT pipeline result into a signed sentiment score."""
        result = sentiment[0]
        label = result["label"]
        sign = {"positive": 1, "negative": -1}.get(label, 0)
        return sign * result["score"]
