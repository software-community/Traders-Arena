"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from dotenv import load_dotenv
load_dotenv()
import os

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func, LargeBinary
import base64
import time


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SESSION_TYPE'] = 'sqlalchemy'
db = SQLAlchemy(app)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_SQLALCHEMY"] = db
Session(app)
            

class Team(db.Model):
    teamID = db.Column(db.Integer, primary_key=True)
    keyCompetition = db.Column(db.Integer, nullable=False) #key competition would be extracted from competitionObj when making comp
    teamName = db.Column(db.String(80), nullable=False)
    teamMembers = db.Column(db.String(200), nullable=False)
    wallet = db.Column(db.Float, default=lambda : Competition.query.order_by(desc(Competition.id)).first().walletSize)
    walletTrend = db.Column(db.String(1000), default = "")
    portfolioTrend = db.Column(db.String(1000), default = "")
    holding = db.Column(db.String(1000), default = "")
    

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.id"), default=lambda: Stock.get_latest_competition_id())
    
    timeIssued = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=5, minutes=30)
    )
    @staticmethod
    def get_latest_competition_id():
        latest_competition = db.session.query(func.max(Competition.id)).scalar()
        return latest_competition if latest_competition else 0  # Return 0 if no competition exists


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_team = db.Column(db.String(80), nullable=False)
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.id"), default=lambda: Stock.get_latest_competition_id())
    seller_team = db.Column(db.String(80), nullable=False)
    roundOfTransaction = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timeOfTransaction = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=5, minutes=30)
    )
    @staticmethod
    def get_latest_competition_id():
        latest_competition = db.session.query(func.max(Competition.id)).scalar()
        return latest_competition if latest_competition else 0  # Return 0 if no competition exists


class Stock_name(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.id"))
    name = db.Column(db.String(80), nullable=False)
    initial_price = db.Column(db.Float, nullable=False)
    rounds = db.relationship(
        "Round", backref="stock_name", cascade="all, delete", lazy=True
    )


class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.id"))
    stock_name_id = db.Column(db.Integer, db.ForeignKey("stock_name.id"))
    price = db.Column(db.Float, nullable=False)


class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=lambda: int(time.time()))
    competitionName = db.Column(db.String(80), nullable=False, unique=True)
    currentRound = db.Column(db.Integer, nullable=False, default=1)
    numberOfRounds = db.Column(db.Integer, nullable=False)
    walletSize = db.Column(db.Float, nullable=False)
    stocks = db.relationship(
        "Stock_name", backref="competition", cascade="all, delete", lazy=True
    )
    timeOfCreation = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=5, minutes=30)
    )


class StockNews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000), nullable=False)
    image = db.Column(LargeBinary)
    content = db.Column(db.Text, nullable=False)
    roundNumber = db.Column(db.Integer, nullable = False)
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.id"), default=lambda: Stock.get_latest_competition_id())

    @staticmethod
    def get_latest_competition_id():
        latest_competition = db.session.query(func.max(Competition.id)).scalar()
        return latest_competition if latest_competition else 0  # Return 0 if no competition exists


def encode_holdings(holdings_dict):
    return ';'.join(f'{stock}:{quantity}' for stock, quantity in holdings_dict.items())

def decode_holdings(holdings_str):
    holdings = {}
    if holdings_str:
        for entry in holdings_str.split(';'):
            stock, quantity = entry.split(':')
            holdings[stock] = int(quantity)
    return holdings



@app.route("/", methods=["GET", "POST"])
def home():
    if session.get('logged_in') != True:
            print("Redirecting to login")
            return redirect("/login")
    print("Redirecting to dashboard")
    return redirect("/dashboard")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get('logged_in'):
            return redirect("/dashboard")
    else:
        user = request.form.get("username")
        users = os.getenv("USERS").split(",")
        password = request.form.get("password")
        actual_password = os.getenv("PASSWORD")
        if user in users and password == actual_password:
            session.update({'logged_in': True})
            print("Successfully Logged In!")
            return redirect("/dashboard")
        else:
            print("Invalid Credentials!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Stock_Admin - portal to add a Competition and involved elements (stocks, wallet size etc)
@app.route("/stock_admin", methods=["GET", "POST"])
def stock_admin():
    if session.get('logged_in') != True:
            return redirect("/login")
    if request.method == "POST":
        competitionName = request.form.get("competitionName")
        numberOfRounds = int(request.form.get("rounds"))
        walletSize = float(request.form.get("walletSize"))
        new_competition = Competition(
            competitionName=competitionName,
            numberOfRounds=numberOfRounds,
            walletSize=walletSize,
        )

        db.session.add(new_competition)
        db.session.commit()

        competition_id = new_competition.id

        stockNames = request.form.getlist("stockName")
        initialPriceList = request.form.getlist("price")

        for i in range(len(stockNames)):
            stock_name = stockNames[i]
            initial_price = float(initialPriceList[i])

            # Add stock name to the database
            new_stock_name = Stock_name(
                competition_id=competition_id,
                name=stock_name,
                initial_price=initial_price,
            )
            db.session.add(new_stock_name)
            db.session.commit()

            # Get the stock_name ID
            stock_name_id = new_stock_name.id

            round_prices = request.form.getlist(f"round-{stockNames[i]}")
            for round_number in range(len(round_prices)):
                price = float(round_prices[round_number])

                # Add round to the database
                new_round = Round(
                    competition_id=competition_id,
                    stock_name_id=stock_name_id,
                    price=price,
                )
                db.session.add(new_round)

        db.session.commit()

        return jsonify({'id': competition_id})
    competitions = Competition.query.all()  # Order by id in descending order

    return render_template("stock_admin.html", competitions=competitions)


# Dashboard to view all added Competitions (and the involved elements - Stocks, Prices etc)
@app.route("/dashboard", methods=["GET", "POST"])
def receive_data():
    if session.get('logged_in') != True:
            return redirect("/login")
    competitions = Competition.query.options(
        joinedload(Competition.stocks).joinedload(Stock_name.rounds)
    ).all()
    
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
            ID = latest_competition.id
    else:
            ID = None

    return render_template("dashboard.html", competitions=competitions, ID=ID)


# Delete Competition from Dashboard
@app.route("/delete-competition", methods=["POST"])
def delete_competition():
    if session.get('logged_in') != True:
            return redirect("/login")
    key_to_delete = request.form.get("keyToDelete")
    competition = Competition.query.options(
        joinedload(Competition.stocks).joinedload(Stock_name.rounds)
    ).get_or_404(key_to_delete)
    db.session.delete(competition)
    db.session.commit()

    return redirect("/dashboard")


@app.route("/initialBuying/<int:ID>", methods=["GET", "POST"])
def stocksIssue(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
        ID = latest_competition.id
    else:
        ID = None

    latest_teams = Team.query.filter(Team.keyCompetition == ID).all()
    latest_stocks = Stock_name.query.filter(Stock_name.competition_id == ID).all()
    currentTeam = None

    if request.method == "POST":
        team = request.form["team"]
        stock = request.form["stock"]
        quantity = request.form["quantity"]
        
        for teamRow in latest_teams:
            if teamRow.teamName == team:
                currentTeam = teamRow
                wallet = teamRow.wallet
                break
        if currentTeam is None:
            print("Team not found:", team)
            return "Team not found"
                  
        stockPrice = None
        for stockRow in latest_stocks:
            if stockRow.name == stock:
                stockPrice = stockRow.initial_price
                break
        if stockPrice is None:
            print("Stock not found:", stock)
            return "Stock not found"
        
        totalPrice = float(quantity) * stockPrice
        if wallet < totalPrice:
            return f"""
            <script>
                alert('Buyer does not have enough funds for this transaction.');
                window.location.href = '/initialBuying/{ID}';
            </script>
            """

        holding_dict = decode_holdings(currentTeam.holding)
        if stock in holding_dict:
            holding_dict[stock] += int(quantity)
        else:
            holding_dict[stock] = int(quantity)
        currentTeam.holding = encode_holdings(holding_dict)
        
        

        new_stock = Stock(team=team, stock=stock, quantity=quantity)
        db.session.add(new_stock)

        currentTeam.wallet -= totalPrice
        currentTeam.walletTrend = f"{currentTeam.wallet}"

        current_round_prices = {
        stock.name: stock.rounds[latest_competition.currentRound - latest_competition.numberOfRounds-1].price for stock in latest_competition.stocks
    }
        
        for team in latest_teams:               
            holdings = decode_holdings(team.holding)
            portfolio_worth = 0
            for stock, quantity in holdings.items():
                if stock in current_round_prices:
                    portfolio_worth += quantity * current_round_prices[stock]
            team.portfolioTrend = f"{portfolio_worth}"

        db.session.commit()

        return redirect(url_for("stocksIssue", ID=ID))

    stocks = Stock.query.filter(Stock.competition_id == ID).order_by(
        Stock.id.desc()
    ).all()  # Order by id in descending order
    return render_template("initialBuying.html", stocks=stocks, ID=ID, latest_teams=latest_teams, latest_stocks=latest_stocks)


# Trading Page
@app.route("/tradingPage/<int:ID>", methods=["GET", "POST"])
def transactions(ID):
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    currentRound = latest_competition.currentRound

    if latest_competition:
            ID = latest_competition.id
    else:
            ID = None
    
    latest_teams = Team.query.filter(Team.keyCompetition == ID).all()
    latest_stocks = Stock_name.query.filter(Stock_name.competition_id == ID).all()


    if request.method == "POST":
        buyer_team = request.form["buyer_team"]
        seller_team = request.form["seller_team"]
        stock = request.form["stock"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        for teamRow in latest_teams:
            if teamRow.teamName == buyer_team:
                buyerTeamObj = teamRow
                buyerWallet = teamRow.wallet
            if teamRow.teamName == seller_team:
                sellerTeamObj = teamRow
                sellerWallet = teamRow.wallet

        total_price = float(quantity) * float(price)

        # Check if the buyer has enough funds
        if total_price > buyerWallet:
            return f"""
            <script>
                alert('Buyer does not have enough funds for this transaction.');
                window.location.href = '/tradingPage/{ID}';
            </script>
            """
        hold = decode_holdings(sellerTeamObj.holding)

        # Check if the seller has enough stock
        if stock not in hold:
            return f"""
            <script>
                alert('Seller does not have these stocks.');
                window.location.href = '/tradingPage/{ID}';
            </script>
            """
        if int(quantity) > hold[stock]:
            return f"""
            <script>
                alert('Seller does not have enough stock for this transaction.');
                window.location.href = '/tradingPage/{ID}';
            </script>
            """
        
        holding_dict1 = decode_holdings(buyerTeamObj.holding)
        if stock in holding_dict1:
            holding_dict1[stock] += int(quantity)
        else:
            holding_dict1[stock] = int(quantity)
        buyerTeamObj.holding = encode_holdings(holding_dict1)
        print(buyerTeamObj.holding)

        holding_dict2 = decode_holdings(sellerTeamObj.holding)
        if stock in holding_dict2:
            holding_dict2[stock] -= int(quantity)
        else:
            holding_dict2[stock] = int(quantity)
        sellerTeamObj.holding = encode_holdings(holding_dict2)
        print(sellerTeamObj.holding)

        new_transaction = Transaction(
            buyer_team=buyer_team,
            seller_team=seller_team,
            stock=stock,
            quantity=quantity,
            price=price,
            roundOfTransaction=currentRound,
        )
        db.session.add(new_transaction)

        buyerTeamObj.wallet -= total_price
        sellerTeamObj.wallet += total_price


        db.session.commit()
        return redirect(url_for("transactions", ID = ID))  # Redirect to avoid form resubmission
    transactions = Transaction.query.filter(Transaction.competition_id == ID).order_by(
        Transaction.id.desc()
    ).all()  # Order by id in descending order
    return render_template("tradingPage.html", transactions=transactions, ID = ID, teams = latest_teams, latest_stocks = latest_stocks, currentRound = currentRound)

# Helper function to calculate portfolio worth
def calculate_portfolio_worth(team, current_round_prices):
    holdings = decode_holdings(team.holding)
    portfolio_worth = 0
    for stock, quantity in holdings.items():
        if stock in current_round_prices:
            portfolio_worth += quantity * current_round_prices[stock]
    return portfolio_worth

@app.route("/updateNext", methods=["POST"])
def next_round():
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    ID = latest_competition.id

    current_round_prices = {
        stock.name: stock.rounds[latest_competition.currentRound - latest_competition.numberOfRounds-1].price for stock in latest_competition.stocks
    }
    print(current_round_prices)

    teams = Team.query.filter(Team.keyCompetition == ID).all()
    for team in teams:

        portfolio_worth = calculate_portfolio_worth(team, current_round_prices)
        print(portfolio_worth)
        team.portfolioTrend += f",{portfolio_worth}"
        team.walletTrend += f",{team.wallet}"
        print("Portfolio","Team :",team,"-",team.portfolioTrend)
        print("Wallet Trend","Team :",team,"-",team.walletTrend)


    # Increment the current round
    latest_competition.currentRound += 1
    db.session.commit()

    if latest_competition.currentRound > latest_competition.numberOfRounds:
        return jsonify({"message": "Competition Over"}), 200
    return jsonify({"message": "Next round started successfully."}), 200

# Page for adding the teams (Shivang)
@app.route("/addTeam/<int:ID>", methods=["GET", "POST"])
def addTeam(ID):
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
            ID = latest_competition.id
    else:
            ID = None
    if request.method == "POST":
        teamName = request.form["teamName"]
        teamMembers = request.form["teamMembers"]
        
        existing_teams = Team.query.filter(Team.keyCompetition == ID).all()
        
        for team in existing_teams:
            if team.teamName == teamName:
                return f"""
                <script>
                    alert('Team name already exists.');
                    window.location.href = '/addTeam/{ID}';
                </script>
                """
        
        newTeam = Team(teamName=teamName, teamMembers=teamMembers, keyCompetition = ID)
        db.session.add(newTeam)
        db.session.commit()
        return redirect(url_for("addTeam", ID = ID))
    
    teams = Team.query.filter(Team.keyCompetition == ID)
    return render_template("addTeam.html", teams=teams, ID = ID)

# Removing the teams (Shivang)
@app.route("/removeTeam", methods=["POST"])
def removeTeam():
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
            ID = latest_competition.id
    else:
            ID = None

    teamID = request.form.get('teamID')
    team = Team.query.get(teamID)
    if team:
        db.session.delete(team)
        db.session.commit()
    return redirect(url_for("addTeam", ID=ID))

@app.route("/compOver/<int:ID>")
def compOver(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    ID = latest_competition.id
    return render_template("CompOver.html", ID = ID)

# Results
@app.route("/results/<int:ID>", methods=["GET"])
def results(ID):
    """ data about each team to be stored in dictionary implemented as 
            - portfolio = {}=> team name: portfolio value information for all rounds as list
            - cash = {}=> team name: cash holdings value for all rounds as list
            - as rounds progress, new portfolio values and cash value to be appended in corresponding lists for each team
            
            - rankings = {}=> this dictionary would be generated at the end of all rounds
    """

    if session.get('logged_in') != True:
            return redirect("/login")
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
        ID = latest_competition.id
    else:
        ID = None

    latestTeams = Team.query.filter(Team.keyCompetition == ID).all()
    names = list(team.teamName for team in latestTeams)
    
    portfolio = {}
    cash = {}
    rankings = {}
    netWorth = {}
    numberOfRounds = latest_competition.numberOfRounds 

    for name in names:
        for team in latestTeams:
            if team.teamName == name:
                portfolio[name] = [0]
                portfolio[name].extend(
                    int(float(value)) for value in team.portfolioTrend.split(",") if value.strip()
                )  # Skip empty strings
                cash[name] = [latest_competition.walletSize]
                cash[name].extend(
                    int(float(value)) for value in team.walletTrend.split(",") if value.strip()
                )  # Skip empty strings
                netWorth[name] = [cash[name][-1] + portfolio[name][-1]]

    netWorth = dict(
        sorted(netWorth.items(), key=lambda item: item[1][-1], reverse=True)[:3]
    )
    for team in netWorth:
        rankings[team] = portfolio[team]
    
    return render_template(
        "results.html",
        portfolio=portfolio,
        cash=cash,
        rankings=rankings,
        numberOfRounds=numberOfRounds,
        netWorth = netWorth,
        ID=ID
    )

@app.route('/stockNews/<int:ID>', methods=["GET", "POST"])
def stockNews(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
        ID = latest_competition.id
        rounds = list(range(1, latest_competition.numberOfRounds + 1))
    else:
        ID = None
        rounds = []
    
    latestNewsLength = len(StockNews.query.filter(StockNews.competition_id == ID).all())
    print(latestNewsLength)

    if request.method == "POST":
        title = request.form.get("title")
        roundNumber = request.form.get("round")
        content = request.form.get("content")
        image_file = request.files['image']  # Get uploaded image file
        image_data = image_file.read() if image_file else None  # Read image data

        newNews = StockNews(
            title=title,
            roundNumber=roundNumber,
            content=content,
            image=image_data,  # Save image data to the database
        )
        db.session.add(newNews)
        db.session.commit()

        return redirect(url_for("stockNews", ID=ID))
    

    print("Rendering stock news page.")
    return render_template('stockNews.html', ID=ID, rounds=rounds, numberOfNews = latestNewsLength)


def slides(ID):
    slides = StockNews.query.filter(StockNews.competition_id == ID).all()
    slides_data = {}
    for slide in slides:
        round_number = str(slide.roundNumber)
        if round_number not in slides_data:
            slides_data[round_number] = []
        img = slide.image
        img = base64.b64encode(img).decode('utf-8')
        slides_data[round_number].append({
            "title": slide.title,
            "content": slide.content,
            "image": img
        })
    return slides_data


def stock_data(ID):
    stock_data = {}
    stocks = Stock_name.query.filter(Stock_name.competition_id == ID).all()
    for stock in stocks:
        if stock.name not in stock_data:
            stock_data[stock.name] = []
        stock_data[stock.name].append(stock.initial_price)
         
    for stock in stocks:
        stockID = stock.id
        stockRound = Round.query.filter(Round.stock_name_id == stockID).all()
        for singleStock in stockRound:
            stock_data[stock.name].append(singleStock.price)
    return stock_data
    

# Updated showNews route
@app.route('/showNews/<int:ID>')
def showNews(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
            ID = latest_competition.id
    else:
            ID = None
    round_number = "1"  # Default round
    stock_data_round = get_stock_data_for_round(round_number, ID)
    return render_template('newsScroll.html', slides=slides(ID)[round_number], rounds=slides(ID).keys(), current_round=round_number, stock_data=stock_data_round, ID = ID)

@app.route('/round/<int:ID>/<round_number>')
def round(ID, round_number):
    if session.get('logged_in') != True:
            return redirect("/login")
    stock_data_round = get_stock_data_for_round(round_number, ID)
    latest_competition = Competition.query.order_by(desc(Competition.id)).first()
    if latest_competition:
            ID = latest_competition.id
    else:
            ID = None
    return render_template('newsScroll.html', slides=slides(ID)[round_number], rounds=slides(ID).keys(), current_round=round_number, stock_data=stock_data_round, ID =ID)

def get_stock_data_for_round(round_number,ID):
    stock_data_round = {stock: values[:int(round_number)] for stock, values in stock_data(ID).items()}
    return stock_data_round


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
