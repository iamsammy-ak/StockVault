import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import datetime, timedelta

def get_stock_data(symbol, period='1mo'):
    """Fetch stock data from IEX Cloud API"""
    api_key = 'YOUR_IEX_API_KEY'  # Replace with your API key
    base_url = f'https://cloud.iexapis.com/stable/stock/{symbol}/chart/{period}?token={api_key}'
    
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return None

def create_stock_chart(symbol, period='1mo'):
    """Create an interactive stock chart using Plotly"""
    df = get_stock_data(symbol, period)
    if df is None:
        return None

    # Create figure with secondary y-axis
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.03, 
                       row_heights=[0.7, 0.3])

    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC'
        ),
        row=1, col=1
    )

    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume'
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        title=f'{symbol} Stock Price',
        yaxis_title='Price',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False,
        height=800
    )

    return fig

def create_portfolio_chart(portfolio_data):
    """Create a portfolio performance chart"""
    fig = go.Figure()

    # Add portfolio value line
    fig.add_trace(
        go.Scatter(
            x=portfolio_data['date'],
            y=portfolio_data['value'],
            mode='lines',
            name='Portfolio Value'
        )
    )

    # Update layout
    fig.update_layout(
        title='Portfolio Performance',
        xaxis_title='Date',
        yaxis_title='Value ($)',
        height=600
    )

    return fig 