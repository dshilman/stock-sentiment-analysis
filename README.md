# stock-sentiment-analysis

```markdown
# Building News Sentiment and Stock Price Performance Analysis NLP Application With Python

In this tutorial, we will explore a fintech idea that combines news sentiment analysis and stock trading to make news more actionable for algorithmic trading. This tutorial presents a step-by-step guide on how to engineer a solution that leverages a market data API and a sentiment score to demonstrate any correlation between news sentiment and stock price performance.

Traders thrive on having instant access to information that enables them to make quick decisions. Consider a scenario where a trader can promptly identify and access news that directly impacts the performance of their stocks, referred to as investor sentiment. However, reading through articles and discerning the content can be time-consuming and may result in missed opportunities. Imagine if traders could receive immediate notifications within their order management software (OMS) whenever a stock they want to trade receives positive media coverage, which could potentially influence the stock price. This idea also presents the opportunity of automating buy/sell decisions by integrating real-time news sentiment scoring into algorithmic strategies.


This application relies on a market data provider that offers stock price history and news feeds. An OMS-embedded market data solution that supports low-latency data streaming, such as Bloomberg Market Data Feed, is best suited for a real-world scenario. The OMS can then highlight securities based on the real-time news and sentiment scores, allowing a trader to make a fast decision.

## Data Sources

For this tutorial, we will acquire a news feed and stock price history from the Mboum Finance API market data provider available on the Rapid API Hub. We will make use of two API endpoints: "stock/history/{stock}/{interval}" for retrieving stock price history and "market/news/{stock}" for obtaining the stock news feed.


## Implementation

Once the user submits the ticker, the form invokes the Python Flask `/analyze` API route. The implementation includes the following logic flow:

1. Retrieve stock news feed from Mboum Finance API.
2. Calculate news sentiment scores using Python's Pandas and Natural Language Processing (NLP) libraries.
3. Visualize sentiment scores using the Plotly library for creating a bar graph.
4. Retrieve the earliest news date to be used to filter out all stock prices outside that period.
5. Retrieve stock price history from Mboum Finance API.
6. Visualize the stock price using the Plotly library for creating a line graph.
7. Change the Headline column to clickable links.
8. Render consolidated results in the `analysis.html` template.


## Result Visualization
![Trading](https://raw.githubusercontent.com/dshilman/stock-sentiment-analysis/master/trading.png)
