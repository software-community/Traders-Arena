# Trader's Arena
Management Portal for FinCom's signature event: Trader's Arena.

## Overview
A Flask-based web application for managing trading competitions, where teams can participate in simulated stock trading events with virtual portfolios.

## Features
- Multi-round trading competitions
- Real-time portfolio tracking
- Stock price management
- Team management
- Transaction history
- Market news updates
- Participant portal with individual dashboards

## Technical Stack
- Backend: Python Flask
- Database: MongoDB
- Frontend: HTML, CSS, JavaScript

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up MongoDB:
- Install MongoDB on your system
- Create a new database named `traders_arena`
- No additional setup required as collections are created automatically

3. Configure Environment:
Create a `.env` file in the root directory with the following variables:
```
MONGODB_URI=mongodb://localhost:27017/traders_arena
USERS=admin,manager  # Comma-separated list of admin usernames
PASSWORD=your_secure_password  # Single password for all admin users
```

4. Run the Application:
```bash
python app.py
```

## Usage

### Admin Portal
1. Access `/login` with credentials from `.env`
2. Create new competitions
3. Add teams and initial portfolios
4. Manage stock prices and rounds
5. Add market news

### Participant Portal
1. Teams login with their unique participant ID
2. View portfolio and transaction history
3. Execute trades during active rounds
4. Track performance across competition rounds

## Development
- Debug mode can be enabled in `app.py`
- MongoDB collections:
  - teams
  - competitions
  - stocks
  - transactions
  - stock_news
  - rounds

## Docker Support
A Dockerfile is included for containerized deployment. Build and run with:
```bash
docker build -t traders-arena .
docker run -p 5000:5000 traders-arena
```