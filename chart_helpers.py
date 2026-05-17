from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import yfinance as yf
from plotly.subplots import make_subplots


def get_stock_data(symbol, period="1mo"):
    """Fetch stock data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception:
        return None


def create_stock_chart(symbol, period="1mo"):
    """Create an interactive stock chart using Plotly."""
    df = get_stock_data(symbol, period)
    if df is None:
        return None

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{symbol} Price", "Volume"),
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    # Moving average line
    df["ma20"] = df["close"].rolling(window=20).mean()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["ma20"],
            mode="lines",
            name="MA 20",
            line=dict(color="#2D72D9", width=1.5),
        ),
        row=1,
        col=1,
    )

    # Volume bar chart
    colors = [
        "#16C784" if df["close"].iloc[i] >= df["open"].iloc[i] else "#EE6C4D"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(x=df["date"], y=df["volume"], name="Volume", marker_color=colors),
        row=2,
        col=1,
    )

    fig.update_layout(
        title=f"{symbol} Stock Price",
        yaxis_title="Price ($)",
        yaxis2_title="Volume",
        xaxis_rangeslider_visible=False,
        height=700,
        template="plotly_white",
        legend=dict(orientation="h", y=1.1),
    )
    fig.update_xaxes(showticklabels=True)
    fig.update_yaxes(showticklabels=True)

    return fig


def create_portfolio_chart(portfolio_data):
    """Create a portfolio performance chart."""
    fig = go.Figure()

    if portfolio_data is None or portfolio_data.empty:
        return fig

    fig.add_trace(
        go.Scatter(
            x=portfolio_data["date"],
            y=portfolio_data["value"],
            mode="lines+markers",
            name="Portfolio Value",
            line=dict(color="#16C784", width=2),
            fill="tozeroy",
            fillcolor="rgba(22,199,132,0.1)",
        )
    )

    fig.update_layout(
        title="Portfolio Performance",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        height=500,
        template="plotly_white",
    )

    return fig
