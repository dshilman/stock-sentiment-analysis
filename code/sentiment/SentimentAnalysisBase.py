"""Base class for sentiment-analysis strategies."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class SentimentAnalysisBase:
    """Common state and plotting for sentiment-analysis implementations.

    Subclasses provide :meth:`calc_sentiment_score` to populate a
    ``sentiment_score`` column on the internal DataFrame.
    """

    def __init__(self) -> None:
        self.symbol: str = ""
        self.df: pd.DataFrame = pd.DataFrame()

    def set_symbol(self, symbol: str) -> None:
        """Set the ticker symbol used in plot titles."""
        self.symbol = symbol

    def set_data(self, df: pd.DataFrame) -> None:
        """Set the news DataFrame to score."""
        self.df = df

    def calc_sentiment_score(self) -> None:
        """Populate ``sentiment_score`` on ``self.df`` (override in subclass)."""

    def get_sentiment_scores(self) -> pd.DataFrame:
        """Return the scored DataFrame."""
        return self.df

    def plot_sentiment(self) -> go.Figure:
        """Return a bar chart of non-zero sentiment scores over time."""
        column = "sentiment_score"
        df_plot = self.df.drop(self.df[self.df[column] == 0].index)

        return px.bar(
            data_frame=df_plot,
            x=df_plot["Date Time"],
            y=column,
            title=f"{self.symbol} Hourly Sentiment Scores",
        )
