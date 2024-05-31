"""
Entrypoint for our management portal
Author: Team SoftCom
"""

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Storing team details
# team = []
class Team(db.Model):
    teamID = db.Column(db.Integer, primary_key=True)
    keyCompetition = db.Column(db.String(80), default="Traders Arena") #key competition would be extracted from competitionObj when making comp
    teamName = db.Column(db.String(80), nullable=False)
    teamMembers = db.Column(db.String(200), nullable=False)


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timeIssued = db.Column(db.DateTime, default=datetime.utcnow)
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_team = db.Column(db.String(80), nullable=False)
    seller_team = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timeOfTransaction = db.Column(db.DateTime, default=datetime.utcnow)


# Competitions are stored as object of this class
class CompetitionObj:
    def __init__(self, competitionName, numberOfRounds, walletSize):
        self.competitionName = competitionName
        self.numberOfRounds = numberOfRounds
        self.walletSize = walletSize
        self.stocks = {}
        self.rounds = {}


# Competition - contains all the added compeititions as (key: Competition Name, value: corresponding object)
Competition = {}


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


# Stock_Admin - portal to add a Competition and involved elements (stocks, wallet size etc)
@app.route("/stock_admin", methods=["GET", "POST"])
def stock_admin():
    if request.method == "POST":
        competitionName = request.form.get("competitionName")
        numberOfRounds = int(request.form.get("rounds"))
        walletSize = request.form.get("walletSize")
        obj = CompetitionObj(competitionName, numberOfRounds, walletSize)

        stockNames = request.form.getlist("stockName")
        priceList = request.form.getlist("price")

        for i in range(len(stockNames)):
            obj.stocks[stockNames[i]] = priceList[i]
            obj.rounds[stockNames[i]] = request.form.getlist(f"round-{stockNames[i]}")

        Competition[competitionName] = obj
        return redirect("/stock_admin")
    return render_template("stock_admin.html", competition=Competition)


# Dashboard to view all added Competitions (and the involved elements - Stocks, Prices etc)
@app.route("/dashboard", methods=["GET", "POST"])
def receive_data():
    return render_template("dashboard.html", competition=Competition)


# Delete Competition from Dashboard
@app.route("/delete-competition", methods=["POST"])
def delete_competition():
    key_to_delete = request.form.get("keyToDelete")
    if key_to_delete in Competition:
        del Competition[key_to_delete]
    return redirect("/dashboard")

# initial buying page
@app.route('/initialBuying', methods=["GET", "POST"])
def stocksIssue():
    if request.method == "POST":
        team = request.form["team"]
        stock = request.form["stock"]
        quantity = request.form["quantity"]
        new_stock = Stock(team=team, stock=stock, quantity=quantity)
        db.session.add(new_stock)
        db.session.commit()
        return redirect(url_for("stocksIssue"))
    stocks = Stock.query.order_by(
        Stock.id.desc()
    ).all()  # Order by id in descending order
    return render_template("initialBuying.html", stocks=stocks)


@app.route("/stock/<int:stock_id>")
def stock_detail(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    return render_template("stock_detail.html", stock=stock)


# To delete issued stock history
@app.route('/delete_stock/<int:stock_id>', methods=["POST"])
def delete_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    return redirect(url_for("stocksIssue"))

# Trading Page
@app.route('/tradingPage', methods=["GET", "POST"])
def transactions():
    if request.method == "POST":
        buyer_team = request.form['buyer_team']
        seller_team = request.form['seller_team']
        stock = request.form['stock']
        quantity = request.form['quantity']
        price = request.form['price']
        
        total_price = float(quantity) * float(price)

        # Get buyer funds from db
        buyer_funds = 1000
        # Get seller stocks form db
        seller_stock = 500

        # Check if the buyer has enough funds
        if total_price > buyer_funds:
            return """
            <script>
                alert('Buyer does not have enough funds for this transaction.');
                window.location.href = 'tradingPage';
            </script>
            """

        # Check if the seller has enough stock
        if int(quantity) > seller_stock:
            return """
            <script>
                alert('Seller does not have enough stock for this transaction.');
                window.location.href = 'tradingPage';
            </script>
            """

        
        new_transaction = Transaction(buyer_team=buyer_team, seller_team=seller_team, stock=stock, quantity=quantity, price=price)
        db.session.add(new_transaction)
        db.session.commit()
        return redirect(url_for('transactions'))  # Redirect to avoid form resubmission
    transactions = Transaction.query.order_by(Transaction.id.desc()).all()  # Order by id in descending order
    return render_template('tradingPage.html', transactions=transactions)

# To delete or undo trades (probably redundant)
@app.route('/delete_transaction/<int:transaction_id>', methods=["POST"])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('transactions'))

# Page for adding the teams (Shivang)
@app.route("/addTeam", methods=["GET", "POST"])
def addTeam():
    if request.method == "POST":
        teamName = request.form["teamName"]
        teamMembers = request.form["teamMembers"]
        
        existing_team = Team.query.filter_by(teamName=teamName).first()
        if existing_team:
            return """
            <script>
                alert('Team name already exists.');
                window.location.href = '/addTeam';
            </script>
            """
        
        newTeam = Team(teamName=teamName, teamMembers=teamMembers)
        db.session.add(newTeam)
        db.session.commit()
        return redirect(url_for("addTeam"))
    
    teams = Team.query.all() 
    return render_template("addTeam.html", teams=teams)


# Removing the teams (Shivang)
@app.route("/removeTeam", methods=["POST"])
def removeTeam():
    teamID = request.form.get('teamID')
    team = Team.query.get(teamID)
    if team:
        db.session.delete(team)
        db.session.commit()
    return redirect(url_for("addTeam"))


# Results
@app.route("/results", methods=["GET"])
def results():
    # dummy team names, later to be replaced by actual team list
    names = [
        "Bullish Blazers",
        "Market Mavericks",
        "Stock Sharks",
        "Trade Titans",
        "Capital Crafters",
        "Profit Prophets",
        "Equity Eagles",
        "Finance Falcons",
        "Wealth Warriors",
        "Investor Innovators",
    ]

    """ data about each team to be stored in dictionary implemented as 
            - portfolio = {}=> team name: portfolio value information for all rounds as list
            - cash = {}=> team name: cash holdings value for all rounds as list
            - as rounds progress, new portfolio values and cash value to be appended in corresponding lists for each team
            
            - rankings = {}=> this dictionary would be generated at the end of all rounds
    """

    portfolio = {}
    cash = {}
    rankings = {}
    numberOfRounds = 8
    for name in names:
        portfolio[name] = [10000]
        portfolio[name].extend(
            [random.randrange(1001, 10000) for _ in range(numberOfRounds)]
        )
        cash[name] = [10000]
        cash[name].extend(
            [
                random.randrange(1000, portfolio[name][x + 1])
                for x in range(numberOfRounds)
            ]
        )
    rankings = dict(
        sorted(portfolio.items(), key=lambda item: item[1][-1], reverse=True)[:3]
    )
    return render_template(
        "results.html",
        portfolio=portfolio,
        cash=cash,
        rankings=rankings,
        numberOfRounds=numberOfRounds,
    )

@app.route('/stockNews')
def stockNews():
    return render_template('stockNews.html')

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
