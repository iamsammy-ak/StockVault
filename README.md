# StockVault — Web-based Stock Trading Platform

> Your gateway to smarter investing.

A sophisticated stock trading platform built with Python and Flask, featuring real-time market data powered by Yahoo Finance — no API key required.

---

## Features

- 📊 **Portfolio Management** — Track holdings with live prices, P&L, and cost basis
- 🔍 **Stock Quotes** — Real-time prices + 1-year interactive growth charts
- 🛒 **Buy / Sell** — Execute trades with transaction safety
- ⭐ **Watchlist** — Track stocks you want to monitor
- 🔒 **Stop-Loss Orders** — Automatic sell triggers at your target price
- 👤 **User Profiles** — Custom display name, bio, and 7-currency support (USD, EUR, GBP, INR, JPY, AUD, CAD)
- 📈 **Interactive Charts** — Candlestick plots with MA20 and volume analysis

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask, Flask-Session |
| Database | SQLite |
| Stock Data | Yahoo Finance (yfinance) — free, no API key |
| Charts | Plotly |
| Frontend | Bootstrap 5, Font Awesome |
| Email | Flask-Mail |
| Scheduler | APScheduler |

---

## Installation

```bash
# Clone the repo
git clone https://github.com/iamsammy-ak/StockVault.git
cd StockVault

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Project Structure

```
StockVault/
├── app.py              # Main Flask application
├── helpers.py          # lookup(), login_required, apology
├── chart_helpers.py    # Plotly chart generation
├── email_helpers.py    # Email verification & reset
├── schema.sql          # Database schema
├── init_db.py          # DB initialization script
├── requirements.txt    # Python dependencies
├── static/
│   └── styles.css      # Custom CSS (Robinhood-inspired theme)
└── templates/           # HTML templates
```

---

## Configuration

Create a `.env` file in the project root (optional — app works without it):

```env
SECRET_KEY=your-random-secret-key
BASE_URL=http://localhost:5000
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

For email functionality, use a Gmail app-specific password: **Google Account → Security → 2-Step Verification → App passwords**.

---

## Data

- New users start with **$10,000 virtual cash**
- All stock data comes from **Yahoo Finance** — free, unlimited, no key needed
- Historical charts use Yahoo Finance 1-year price history

---

## License

MIT License — free to use, modify, and distribute.

---

Built with ❤️ by **Abhishek Kumar**