import sqlite3

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    # Drop existing tables
    c.executescript("""
        DROP TABLE IF EXISTS user_profiles;
        DROP TABLE IF EXISTS stop_loss_orders;
        DROP TABLE IF EXISTS watchlist;
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS stock_quotes;
    """)

    # Read and execute schema.sql
    with open('schema.sql', 'r') as f:
        schema = f.read()
        c.executescript(schema)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!") 