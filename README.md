# StockVault - Web-based Stock Trading Platform
#### Video Demo: https://youtu.be/Hba0euLa0JE

## Description

StockVault is a sophisticated web-based stock trading platform that empowers users to manage their investment portfolios with professional-grade tools and real-time market data. Built with Python and Flask, this application combines robust backend functionality with an intuitive user interface to deliver a seamless trading experience.

The project was born from the need to create a comprehensive yet accessible platform for both novice and experienced investors. While there are many stock trading platforms available, StockVault distinguishes itself through its combination of real-time data integration, user-friendly interface, and advanced portfolio management features.

## Core Components and Design Decisions

### Backend Architecture
The application's backend is built using Flask, chosen for its lightweight nature and flexibility. The decision to use Flask over Django was made to maintain a more modular and customizable codebase. The backend is structured into several key components:

- **Models**: The database models (`models/`) handle all data persistence using SQLAlchemy ORM. This choice was made to ensure type safety and maintainable database operations. The models include User, Portfolio, Transaction, and Watchlist entities, each carefully designed to maintain data integrity and relationships.

- **Routes**: The routing system (`routes/`) implements RESTful API endpoints, following best practices for web application development. Each route is designed to handle specific functionality while maintaining separation of concerns.

- **Authentication**: A custom authentication system was implemented using Flask-Login, providing secure user management with features like email verification and password reset. This was chosen over third-party authentication to maintain full control over the user experience and security measures.

### Frontend Implementation
The frontend is built using a combination of HTML, CSS, and JavaScript, with Bootstrap for responsive design. Key design decisions include:

- **Real-time Updates**: WebSocket integration was implemented for real-time stock price updates, chosen over polling to reduce server load and provide instant feedback to users.

- **Interactive Charts**: The platform uses Chart.js for data visualization, selected for its performance and customization options. This allows users to view historical data and portfolio performance in an intuitive manner.

- **Responsive Design**: The UI is fully responsive, ensuring a consistent experience across devices. This was a crucial design decision to accommodate users who might want to monitor their portfolio on mobile devices.

### Key Features and Implementation Details

#### Portfolio Management
The portfolio management system is the heart of StockVault. It includes:
- Real-time value tracking using Finnhub API integration
- Performance analytics with customizable timeframes
- Position tracking with detailed entry/exit points
- Risk management tools including stop-loss orders

The decision to implement real-time tracking was made to provide users with accurate, up-to-the-minute portfolio valuations, crucial for making informed trading decisions.

#### Stock Information System
The stock information system provides comprehensive market data:
- Real-time price updates
- Historical data visualization
- Company financials and news
- Technical indicators

This system was designed to give users all the information they need to make informed decisions without overwhelming them with unnecessary data.

#### Watchlist Feature
The watchlist system allows users to:
- Create multiple watchlists for different strategies
- Set custom alerts for price movements
- Track potential investments
- Share watchlists with other users

This feature was implemented to help users organize their research and potential investments more effectively.

## Technical Challenges and Solutions

### Data Management
One of the biggest challenges was handling real-time stock data efficiently. The solution involved:
- Implementing a caching system to reduce API calls
- Using WebSocket connections for live updates
- Optimizing database queries for performance

### Security Considerations
Security was a top priority in the development process:
- Implemented CSRF protection
- Used secure password hashing
- Implemented rate limiting
- Added input validation and sanitization

## Future Enhancements

The project is designed to be extensible, with planned features including:
- Advanced order types
- Social trading features
- Machine learning-based market predictions
- Mobile application development

## Features

- Real-time stock data tracking
- User authentication and profile management
- Portfolio management and performance tracking
- Stock search and detailed information
- Transaction history
- Email verification
- Password reset functionality
- Watchlist feature
- Stop-loss orders
- User profile customization

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- Modern web browser
- For Windows users:
  - Visual Studio Build Tools with "Desktop development with C++" workload
  - This is required for building some Python packages with C extensions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stockportfolio.git
cd stockportfolio
```

2. Create and activate a virtual environment:
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Start the development server:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Configuration

1. Create a `.env` file in the project root with the following variables:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///stockportfolio.db
FINNHUB_API_KEY=your-api-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

2. Get an API key from [Finnhub](https://finnhub.io/) for stock data
3. For email functionality, set up an app-specific password for your Gmail account

## Project Structure

```
stockportfolio/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── migrations/
├── instance/
├── tests/
├── .env
├── .gitignore
├── config.py
├── requirements.txt
└── README.md
```

## Features in Detail

### User Authentication
- Secure registration and login system
- Email verification for new accounts
- Password reset functionality
- Session management

### Portfolio Management
- Real-time portfolio value tracking
- Performance metrics and charts
- Transaction history
- Position tracking

### Stock Information
- Real-time stock data
- Historical price charts
- Company information
- News and updates

### Watchlist
- Create and manage multiple watchlists
- Add/remove stocks from watchlists
- Real-time price updates for watched stocks

### Stop-Loss Orders
- Set stop-loss orders for positions
- Automatic order execution
- Order management interface

### User Profile
- Customizable profile information
- Portfolio preferences
- Notification settings
- Theme customization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Finnhub for stock market data
- Flask framework and its extensions
- Bootstrap for the frontend design
- All contributors and users of the project 