import json
import os
import sqlite3

import pandas as pd
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, flash, g, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from chart_helpers import create_portfolio_chart, create_stock_chart
from email_helpers import (
    init_mail,
    send_password_reset_email,
    send_verification_email,
    verify_token,
)
from flask_session import Session
from helpers import apology, login_required, lookup, usd

# Load environment variables
load_dotenv()

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

AVAILABLE_STOCKS = [
    # US
    {"symbol": "AAPL", "name": "Apple Inc."},
    {"symbol": "MSFT", "name": "Microsoft Corp."},
    {"symbol": "GOOGL", "name": "Alphabet Inc."},
    {"symbol": "AMZN", "name": "Amazon.com Inc."},
    {"symbol": "TSLA", "name": "Tesla Inc."},
    {"symbol": "META", "name": "Meta Platforms Inc."},
    {"symbol": "NVDA", "name": "Nvidia Corp."},
    # Europe
    {"symbol": "SAP", "name": "SAP SE (Germany)"},
    {"symbol": "ASML", "name": "ASML Holding (Netherlands)"},
    {"symbol": "SIEGY", "name": "Siemens AG (Germany)"},
    {"symbol": "NESN", "name": "Nestle SA (Switzerland)"},
    {"symbol": "AIR", "name": "Airbus SE (France)"},
    {"symbol": "OR", "name": "L'Oreal (France)"},
    # India
    {"symbol": "RELIANCE.BSE", "name": "Reliance Industries (India)"},
    {"symbol": "TCS.BSE", "name": "Tata Consultancy Services (India)"},
    {"symbol": "INFY.BSE", "name": "Infosys (India)"},
    {"symbol": "HDFCBANK.BSE", "name": "HDFC Bank (India)"},
    {"symbol": "HINDUNILVR.BSE", "name": "Hindustan Unilever (India)"},
    {"symbol": "ICICIBANK.BSE", "name": "ICICI Bank (India)"},
]

# Currency conversion rates (you should use a real API in production)
CURRENCY_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.0,
    "JPY": 151.0,
    "AUD": 1.52,
    "CAD": 1.36,
}


def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    usd_amount = amount / CURRENCY_RATES[from_currency]
    return usd_amount * CURRENCY_RATES[to_currency]


def format_currency(amount, currency):
    """Format amount according to currency"""
    if amount is None:
        amount = 0
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    elif currency == "GBP":
        return f"£{amount:,.2f}"
    elif currency == "INR":
        return f"₹{amount:,.2f}"
    elif currency == "JPY":
        return f"¥{amount:,.0f}"
    elif currency == "AUD":
        return f"A${amount:,.2f}"
    elif currency == "CAD":
        return f"C${amount:,.2f}"
    return f"{amount:,.2f}"


# Add custom filter for currency formatting
app.jinja_env.filters["format_currency"] = format_currency

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure email
init_mail(app)

# Set secret key for token generation
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["BASE_URL"] = os.getenv("BASE_URL", "http://localhost:5000")

# Initialize database


# Initialize database (only if tables don't exist — safe to call on every start)
with sqlite3.connect("finance.db") as conn:
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not c.fetchone():
        conn.executescript(open("schema.sql").read())
    conn.commit()


# Configure SQLite database
def get_db():
    db = sqlite3.connect("finance.db", timeout=30)
    db.row_factory = sqlite3.Row
    return db


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks and available stocks with live prices"""
    db = get_db()
    # Get user's cash balance and currency preference
    user = db.execute(
        """
        SELECT u.cash, p.currency
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    """,
        (session["user_id"],),
    ).fetchone()

    if not user:
        return apology("User not found.")
    cash = user["cash"]
    currency = user["currency"] or "USD"

    # Get user's stocks
    stocks = db.execute(
        """
        SELECT symbol, SUM(shares) as total_shares, AVG(price) as avg_price
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING total_shares > 0
    """,
        (session["user_id"],),
    ).fetchall()

    # Calculate total value of portfolio (holdings only, not cash)
    total = 0
    cost_basis = 0
    portfolio = []
    for stock in stocks:
        quote = lookup(stock["symbol"])
        if quote:
            stock_dict = dict(stock)
            stock_dict["shares"] = stock["total_shares"]
            stock_dict["avg_price"] = (
                stock["avg_price"] if "avg_price" in stock.keys() else 0
            )
            # Convert price to user's preferred currency
            price = convert_currency(quote["price"], "USD", currency)
            stock_dict["price"] = price
            stock_dict["name"] = quote["name"]
            stock_dict["total"] = price * stock["total_shares"]
            total += stock_dict["total"]
            portfolio.append(stock_dict)

            # --- Calculate cost basis for this stock (FIFO) ---
            # Get all transactions for this stock, ordered by timestamp
            txs = db.execute(
                """
                SELECT shares, price FROM transactions
                WHERE user_id = ? AND symbol = ?
                ORDER BY timestamp ASC, id ASC
                """,
                (session["user_id"], stock["symbol"]),
            ).fetchall()
            shares_left = stock["total_shares"]
            tx_index = 0
            for tx in txs:
                if shares_left <= 0:
                    break
                if tx["shares"] > 0:
                    # Buy transaction
                    take = min(tx["shares"], shares_left)
                    cost_basis += take * convert_currency(tx["price"], "USD", currency)
                    shares_left -= take
                else:
                    # Sell transaction, skip for cost basis
                    continue

    # Live available stocks (from centralized constant)
    available_stocks_live = []
    for stock in AVAILABLE_STOCKS:
        quote = lookup(stock["symbol"])
        available_stocks_live.append(
            {
                "symbol": stock["symbol"],
                "name": stock["name"],
                "price": quote["price"] if quote and "price" in quote else None,
            }
        )

    # Convert cash to user's preferred currency
    cash = convert_currency(cash, "USD", currency)
    total = convert_currency(total, "USD", currency)

    # Calculate portfolio change (gain/loss)
    portfolio_change = total - cost_basis

    return render_template(
        "index.html",
        stocks=portfolio,
        cash=cash,
        total_value=total,
        currency=currency,
        available_stocks=available_stocks_live,
        cost_basis=cost_basis,
        portfolio_change=portfolio_change,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must provide symbol")
        if not shares:
            return apology("must provide number of shares")
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("shares must be positive")
        except ValueError:
            return apology("shares must be a number")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol")

        db = get_db()
        user = db.execute(
            "SELECT cash FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        cost = quote["price"] * shares

        if user["cash"] < cost:
            return apology("Not enough credit. Please add funds to your account.")

        try:
            db.execute(
                "UPDATE users SET cash = cash - ? WHERE id = ?",
                (cost, session["user_id"]),
            )
            db.execute(
                """
                INSERT INTO transactions (user_id, symbol, shares, price)
                VALUES (?, ?, ?, ?)
            """,
                (session["user_id"], symbol.upper(), shares, quote["price"]),
            )
            db.commit()
        except Exception:
            db.rollback()
            return apology("Transaction failed. Please try again.")

        flash("Bought!")
        return redirect("/")

    return render_template("buy.html", available_stocks=AVAILABLE_STOCKS)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    db = get_db()
    transactions = db.execute(
        """
        SELECT symbol, shares, price, timestamp
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """,
        (session["user_id"],),
    ).fetchall()
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username")
        elif not request.form.get("password"):
            return apology("must provide password")

        db = get_db()
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password")

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote with 1-year price history chart."""
    symbol = request.args.get("symbol") or request.form.get("symbol")
    quote_data = None
    history = []
    error = None

    if symbol:
        quote_data = lookup(symbol)
        if not quote_data:
            error = f"No data found for symbol '{symbol}'"
        else:
            try:
                ticker = yf.Ticker(symbol.upper())
                hist = ticker.history(period="1y")
                if hist.empty:
                    error = "No historical data found."
                else:
                    hist = hist.reset_index()
                    hist.columns = [c.lower() for c in hist.columns]
                    history = [
                        {"date": str(row.name.date()), "close": round(row["close"], 2)}
                        for _, row in hist.iterrows()
                    ]
            except Exception:
                error = "Could not load historical data."

    return render_template(
        "quote.html", quote=quote_data, history=history, error=error, symbol=symbol
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username")
        elif not password:
            return apology("must provide password")
        elif not confirmation:
            return apology("must provide password confirmation")
        elif password != confirmation:
            return apology("passwords do not match")

        db = get_db()
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchall()
        if len(rows) > 0:
            return apology("username already exists")

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()

        # Create user profile with default currency
        user_id = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO user_profiles (user_id, currency) VALUES (?, ?)",
            (user_id, "USD"),
        )
        db.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    db = get_db()
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must provide symbol")
        if not shares:
            return apology("must provide number of shares")
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("shares must be positive")
        except ValueError:
            return apology("shares must be a number")

        # Check if user has enough shares
        stock = db.execute(
            """
            SELECT SUM(shares) as total_shares
            FROM transactions
            WHERE user_id = ? AND symbol = ?
            GROUP BY symbol
        """,
            (session["user_id"], symbol),
        ).fetchone()

        if not stock or stock["total_shares"] < shares:
            return apology("not enough shares")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol")

        # Execute sell
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            (quote["price"] * shares, session["user_id"]),
        )
        db.execute(
            """
            INSERT INTO transactions (user_id, symbol, shares, price)
            VALUES (?, ?, ?, ?)
        """,
            (session["user_id"], symbol.upper(), -shares, quote["price"]),
        )
        db.commit()
        flash("Sold!")
        return redirect("/")

    # Get user's stocks for the form
    stocks = db.execute(
        """
        SELECT symbol, SUM(shares) as total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING total_shares > 0
    """,
        (session["user_id"],),
    ).fetchall()

    # Convert Row objects to dictionaries
    portfolio = [dict(stock) for stock in stocks]
    return render_template("sell.html", stocks=portfolio)


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Add cash to user's account"""
    if request.method == "POST":
        amount = request.form.get("amount")
        if not amount:
            return apology("must provide amount")
        try:
            amount = float(amount)
            if amount <= 0:
                return apology("amount must be positive")
        except ValueError:
            return apology("amount must be a number")

        db = get_db()
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            (amount, session["user_id"]),
        )
        db.commit()

        flash("Cash added successfully!")
        return redirect("/")

    return render_template("add_cash.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user's password"""
    if request.method == "POST":
        current = request.form.get("current_password")
        new = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not current:
            return apology("must provide current password")
        elif not new:
            return apology("must provide new password")
        elif not confirmation:
            return apology("must provide password confirmation")
        elif new != confirmation:
            return apology("new passwords do not match")

        db = get_db()
        user = db.execute(
            "SELECT hash FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

        if not check_password_hash(user["hash"], current):
            return apology("current password is incorrect")

        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            (generate_password_hash(new), session["user_id"]),
        )
        db.commit()

        flash("Password changed successfully!")
        return redirect("/")

    return render_template("change_password.html")


@app.route("/verify-email/<token>")
def verify_email(token):
    """Verify user's email address"""
    email = verify_token(token)
    if email is None:
        flash("Invalid or expired verification link")
        return redirect("/")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if user is None:
        flash("User not found")
        return redirect("/")

    if user["email_verified"]:
        flash("Email already verified")
        return redirect("/")

    db.execute(
        """
        UPDATE users
        SET email_verified = TRUE, verification_token = NULL
        WHERE email = ?
    """,
        (email,),
    )
    db.commit()

    flash("Email verified successfully!")
    return redirect("/")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password_request():
    """Handle password reset requests"""
    if request.method == "POST":
        email = request.form.get("email")
        if not email:
            return apology("must provide email")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user:
            send_password_reset_email(email)
            flash("Password reset instructions sent to your email")
            return redirect("/login")

        flash("Email not found")
        return redirect("/reset-password")

    return render_template("reset_password_request.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset user's password"""
    email = verify_token(token)
    if email is None:
        flash("Invalid or expired reset link")
        return redirect("/")

    if request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not password:
            return apology("must provide password")
        elif not confirmation:
            return apology("must provide password confirmation")
        elif password != confirmation:
            return apology("passwords do not match")

        db = get_db()
        db.execute(
            """
            UPDATE users
            SET hash = ?, reset_token = NULL, reset_token_expiry = NULL
            WHERE email = ?
        """,
            (generate_password_hash(password), email),
        )
        db.commit()

        flash("Password reset successful!")
        return redirect("/login")

    return render_template("reset_password.html")


@app.route("/watchlist")
@login_required
def watchlist():
    """Show user's watchlist"""
    db = get_db()
    watchlist_items = db.execute(
        """
        SELECT w.*, l.name as company_name, l.price, l.change
        FROM watchlist w
        LEFT JOIN (
            SELECT symbol, name, price, change
            FROM (
                SELECT symbol, name, price, change,
                       ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
                FROM stock_quotes
            ) t
            WHERE rn = 1
        ) l ON w.symbol = l.symbol
        WHERE w.user_id = ?
        ORDER BY w.added_at DESC
    """,
        (session["user_id"],),
    ).fetchall()

    return render_template("watchlist.html", watchlist=watchlist_items)


@app.route("/watchlist/add", methods=["POST"])
@login_required
def add_to_watchlist():
    data = request.get_json() or {}
    symbol = data.get("symbol") or request.form.get("symbol")
    if not symbol:
        return jsonify({"success": False, "error": "must provide symbol"}), 400

    quote = lookup(symbol)
    if not quote:
        return jsonify({"success": False, "error": "invalid symbol"}), 400

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO watchlist (user_id, symbol)
            VALUES (?, ?)
        """,
            (session["user_id"], symbol.upper()),
        )
        # Insert or update stock_quotes
        db.execute(
            """
            INSERT INTO stock_quotes (symbol, name, price, change)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                price=excluded.price,
                change=excluded.change,
                last_updated=CURRENT_TIMESTAMP
        """,
            (
                quote.get("symbol", symbol.upper()),
                quote.get("name", symbol.upper()),
                quote.get("price", 0),
                quote.get("change", 0),
            ),
        )
        db.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify(
            {
                "success": False,
                "error": f"{symbol.upper()} is already in your watchlist",
            }
        ), 400


@app.route("/watchlist/remove", methods=["POST"])
@login_required
def remove_from_watchlist():
    # Get symbol from JSON body or form data
    data = request.get_json() or {}
    symbol = data.get("symbol") or request.form.get("symbol")
    if not symbol:
        return jsonify({"success": False, "error": "must provide symbol"}), 400

    db = get_db()
    db.execute(
        """
        DELETE FROM watchlist
        WHERE user_id = ? AND symbol = ?
    """,
        (session["user_id"], symbol.upper()),
    )
    db.commit()

    return jsonify({"success": True})


@app.route("/stop-loss")
@login_required
def stop_loss():
    """Show stop-loss orders"""
    db = get_db()
    active_orders = db.execute(
        """
        SELECT s.*, l.price as current_price
        FROM stop_loss_orders s
        LEFT JOIN (
            SELECT symbol, price
            FROM (
                SELECT symbol, price,
                       ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
                FROM stock_quotes
            ) t
            WHERE rn = 1
        ) l ON s.symbol = l.symbol
        WHERE s.user_id = ? AND s.status = 'active'
        ORDER BY s.created_at DESC
    """,
        (session["user_id"],),
    ).fetchall()

    order_history = db.execute(
        """
        SELECT *
        FROM stop_loss_orders
        WHERE user_id = ? AND status != 'active'
        ORDER BY created_at DESC
    """,
        (session["user_id"],),
    ).fetchall()

    return render_template(
        "stop_loss.html", active_orders=active_orders, order_history=order_history
    )


@app.route("/stop-loss/create", methods=["POST"])
@login_required
def create_stop_loss():
    """Create a stop-loss order"""
    symbol = request.form.get("symbol")
    shares = request.form.get("shares")
    trigger_price = request.form.get("trigger_price")

    if not all([symbol, shares, trigger_price]):
        return apology("must provide all fields")

    try:
        shares = int(shares)
        trigger_price = float(trigger_price)
        if shares <= 0 or trigger_price <= 0:
            return apology("invalid values")
    except ValueError:
        return apology("invalid values")

    quote = lookup(symbol)
    if not quote:
        return apology("invalid symbol")

    db = get_db()
    # Check if user has enough shares
    user_shares = db.execute(
        """
        SELECT SUM(shares) as total_shares
        FROM transactions
        WHERE user_id = ? AND symbol = ?
        GROUP BY symbol
    """,
        (session["user_id"], symbol.upper()),
    ).fetchone()

    if not user_shares or user_shares["total_shares"] < shares:
        return apology("not enough shares")

    db.execute(
        """
        INSERT INTO stop_loss_orders (user_id, symbol, shares, trigger_price)
        VALUES (?, ?, ?, ?)
    """,
        (session["user_id"], symbol.upper(), shares, trigger_price),
    )
    db.commit()

    flash("Stop-loss order created")
    return redirect("/stop-loss")


@app.route("/stop-loss/cancel", methods=["POST"])
@login_required
def cancel_stop_loss():
    """Cancel a stop-loss order"""
    order_id = request.form.get("order_id")
    if not order_id:
        return apology("must provide order ID")

    db = get_db()
    db.execute(
        """
        UPDATE stop_loss_orders
        SET status = 'cancelled'
        WHERE id = ? AND user_id = ? AND status = 'active'
    """,
        (order_id, session["user_id"]),
    )
    db.commit()

    flash("Stop-loss order cancelled")
    return redirect("/stop-loss")


@app.route("/profile")
@login_required
def profile():
    """Show user profile"""
    db = get_db()
    user = db.execute(
        """
        SELECT u.*, p.*
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    """,
        (session["user_id"],),
    ).fetchone()

    return render_template("profile.html", user=user, profile=user)


@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Update user profile"""
    display_name = request.form.get("display_name")
    bio = request.form.get("bio")

    db = get_db()
    # Check if profile exists
    profile = db.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?", (session["user_id"],)
    ).fetchone()

    if profile:
        db.execute(
            """
            UPDATE user_profiles
            SET display_name = ?, bio = ?
            WHERE user_id = ?
        """,
            (display_name, bio, session["user_id"]),
        )
    else:
        db.execute(
            """
            INSERT INTO user_profiles (user_id, display_name, bio)
            VALUES (?, ?, ?)
        """,
            (session["user_id"], display_name, bio),
        )

    db.commit()
    flash("Profile updated")
    return redirect("/profile")


@app.route("/profile/preferences", methods=["POST"])
@login_required
def update_preferences():
    """Update user preferences"""
    theme = request.form.get("theme")
    notifications = request.form.get("notifications") == "on"

    db = get_db()
    # Check if profile exists
    profile = db.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?", (session["user_id"],)
    ).fetchone()

    if profile:
        db.execute(
            """
            UPDATE user_profiles
            SET theme = ?, notifications_enabled = ?
            WHERE user_id = ?
        """,
            (theme, notifications, session["user_id"]),
        )
    else:
        db.execute(
            """
            INSERT INTO user_profiles (user_id, theme, notifications_enabled)
            VALUES (?, ?, ?)
        """,
            (session["user_id"], theme, notifications),
        )

    db.commit()
    flash("Preferences updated")
    return redirect("/profile")


@app.route("/chart/<symbol>")
@login_required
def stock_chart(symbol):
    """Show stock chart"""
    period = request.args.get("period", "1mo")
    chart = create_stock_chart(symbol, period)

    if chart is None:
        return apology("Could not generate chart")

    return render_template("chart.html", chart=chart.to_html(full_html=False))


@app.route("/portfolio/chart")
@login_required
def portfolio_chart():
    """Show portfolio performance chart"""
    db = get_db()
    # Get portfolio value history
    portfolio_data = db.execute(
        """
        SELECT
            date(timestamp) as date,
            SUM(CASE
                WHEN shares > 0 THEN shares * price
                ELSE -shares * price
            END) as value
        FROM transactions
        WHERE user_id = ?
        GROUP BY date(timestamp)
        ORDER BY date
    """,
        (session["user_id"],),
    ).fetchall()

    # Convert to DataFrame format
    df = pd.DataFrame(portfolio_data)
    chart = create_portfolio_chart(df)

    if chart is None:
        return apology("Could not generate chart")

    return render_template("portfolio_chart.html", chart=chart.to_html(full_html=False))


@app.route("/change-currency", methods=["POST"])
@login_required
def change_currency():
    """Change user's preferred currency"""
    data = request.get_json()
    currency = data.get("currency")

    if currency not in CURRENCY_RATES:
        return jsonify({"success": False, "error": "Invalid currency"})

    db = get_db()
    db.execute(
        """
        UPDATE user_profiles
        SET currency = ?
        WHERE user_id = ?
    """,
        (currency, session["user_id"]),
    )
    db.commit()

    return jsonify({"success": True})


@app.context_processor
def inject_profile():
    profile = None
    if "user_id" in session:
        db = get_db()
        user = db.execute(
            """
            SELECT u.username, p.currency, p.display_name
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = ?
        """,
            (session["user_id"],),
        ).fetchone()
        if user:
            profile = {
                "currency": user["currency"] or "USD",
                "display_name": user["display_name"] or user["username"],
            }
    if not profile:
        profile = {"currency": "USD", "display_name": ""}
    return dict(profile=profile)


@app.route("/api/quote")
@login_required
def api_quote():
    symbol = request.args.get("symbol")
    if not symbol:
        return {"error": "No symbol provided"}, 400
    quote = lookup(symbol)
    if not quote:
        return {"error": "Invalid symbol"}, 404
    return {
        "symbol": quote.get("symbol", symbol),
        "name": quote.get("name", symbol),
        "price": quote.get("price", 0),
    }


# Background scheduler for stop-loss order execution
def check_stop_loss_orders():
    """Check and execute stop-loss orders (runs in background scheduler)."""
    with app.app_context():
        db = get_db()
        try:
            active_orders = db.execute("""
                SELECT s.*, l.price as current_price
                FROM stop_loss_orders s
                LEFT JOIN (
                    SELECT symbol, price
                    FROM (
                        SELECT symbol, price,
                               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY last_updated DESC) as rn
                        FROM stock_quotes
                    ) t
                    WHERE rn = 1
                ) l ON s.symbol = l.symbol
                WHERE s.status = 'active'
            """).fetchall()

            for order in active_orders:
                if (
                    order["current_price"]
                    and order["current_price"] <= order["trigger_price"]
                ):
                    db.execute(
                        """INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)""",
                        (
                            order["user_id"],
                            order["symbol"],
                            -order["shares"],
                            order["current_price"],
                        ),
                    )
                    db.execute(
                        "UPDATE stop_loss_orders SET status = 'executed' WHERE id = ?",
                        (order["id"],),
                    )
                    db.execute(
                        "UPDATE users SET cash = cash + ? WHERE id = ?",
                        (order["shares"] * order["current_price"], order["user_id"]),
                    )
            db.commit()
        except Exception as e:
            print(f"Stop-loss check error: {e}")
            db.rollback()
        finally:
            db.close()


if __name__ == "__main__":
    # Start the background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_stop_loss_orders, "interval", minutes=1)
    scheduler.start()
    app.run(debug=True)
