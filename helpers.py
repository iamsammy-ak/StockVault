from functools import wraps

import yfinance as yf
from flask import redirect, render_template, session


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
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
    """Look up quote for symbol using Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.fast_info

        price = getattr(info, "last_price", None) or getattr(info, "lastPrice", None)
        if price is None:
            return None

        prev_close = (
            getattr(info, "previous_close", None)
            or getattr(info, "previousClose", None)
            or price
        )
        change_amount = price - prev_close
        change_pct = (change_amount / prev_close * 100) if prev_close else 0

        return {
            "symbol": symbol.upper(),
            "name": getattr(info, "long_name", None)
            or getattr(info, "longName", symbol.upper()),
            "price": round(float(price), 2),
            "change": round(float(change_pct), 2),
            "change_amount": round(float(change_amount), 2),
            "high": round(
                float(
                    getattr(info, "day_high", None) or getattr(info, "dayHigh", price)
                ),
                2,
            ),
            "low": round(
                float(getattr(info, "day_low", None) or getattr(info, "dayLow", price)),
                2,
            ),
            "volume": int(
                getattr(info, "last_volume", None)
                or getattr(info, "lastVolume", 0)
                or 0
            ),
            "market_cap": getattr(info, "market_cap", None)
            or getattr(info, "marketCap", None),
            "pe_ratio": getattr(info, "trailing_pe", None)
            or getattr(info, "trailingPE", None),
            "year_high": round(
                float(
                    getattr(info, "fifty_two_week_high", None)
                    or getattr(info, "yearHigh", price)
                ),
                2,
            ),
            "year_low": round(
                float(
                    getattr(info, "fifty_two_week_low", None)
                    or getattr(info, "yearLow", price)
                ),
                2,
            ),
        }
    except Exception as e:
        print(f"Error looking up {symbol}: {e}")
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
