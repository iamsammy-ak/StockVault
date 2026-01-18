import os
import requests
from functools import wraps
from flask import redirect, render_template, session


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using Finnhub."""
    try:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            raise ValueError("FINNHUB_API_KEY environment variable is not set")
            
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if "c" in data and data["c"] != 0:
            return {
                "symbol": symbol.upper(),
                "name": symbol.upper(),  # Finnhub free API does not provide company name
                "price": float(data["c"]),
                "change": float(data["dp"]),  # Daily percentage change
                "change_amount": float(data["d"]),  # Daily change amount
                "high": float(data["h"]),  # High price of the day
                "low": float(data["l"]),  # Low price of the day
                "volume": int(data["v"])  # Trading volume
            }
        return None
    except Exception as e:
        print(f"Error looking up {symbol}: {str(e)}")
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
