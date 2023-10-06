import plotly.express as px
import plotly.graph_objects as go


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

    def calc_sentiment_score(self):
        pass

    def plot_sentiment(self) -> go.Figure:

        column = 'sentiment_score'

        df_plot = self.df.drop(
            self.df[self.df[f'{column}'] == 0].index)

        fig = px.bar(data_frame=df_plot, x=df_plot['Date Time'], y=f'{column}',
                     title=f"{self.symbol} Hourly Sentiment Scores")
        return fig
