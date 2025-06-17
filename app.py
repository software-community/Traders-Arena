"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from dotenv import load_dotenv
load_dotenv()
import os
import random
import string
from datetime import datetime, timedelta
from bson import ObjectId

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_pymongo import PyMongo
from flask_session import Session
import base64
import time

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/traders_arena")
app.config['SESSION_TYPE'] = 'mongodb'
mongo = PyMongo(app)
app.config["SESSION_MONGODB"] = mongo.db
server_name = os.getenv("SERVER_NAME")
if server_name:
    app.config["SERVER_NAME"] = server_name
Session(app)

def generate_team_id():
    # Generate a random 6-character alphanumeric ID
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# MongoDB Collections
teams = mongo.db.teams
stocks = mongo.db.stocks
transactions = mongo.db.transactions
stock_names = mongo.db.stock_names
rounds = mongo.db.rounds
competitions = mongo.db.competitions
stock_news = mongo.db.stock_news

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
            session.update({'logged_in': True, 'user': user})
            print("Successfully Logged In!")
            return redirect("/dashboard")
        else:
            print("Invalid Credentials!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/stock_admin", methods=["GET", "POST"])
def stock_admin():
    if session.get('logged_in') != True:
            return redirect("/login")
    if request.method == "POST":
        print("Received POST request to stock_admin")
        print("Form data:", request.form)
        
        competitionName = request.form.get("competitionName")
        # Check for duplicate competition name
        existing = competitions.find_one({"competitionName": competitionName})
        if existing:
            return jsonify({'error': 'Competition name already exists. Please choose a different name.'}), 400
        
        numberOfRounds = int(request.form.get("rounds"))
        walletSize = float(request.form.get("walletSize"))
        
        print(f"Competition: {competitionName}, Rounds: {numberOfRounds}, Wallet: {walletSize}")
        
        competition_id = int(time.time())
        new_competition = {
            "_id": competition_id,
            "competitionName": competitionName,
            "numberOfRounds": numberOfRounds,
            "walletSize": walletSize,
            "currentRound": 1,
            "timeOfCreation": datetime.utcnow() + timedelta(hours=5, minutes=30)
        }

        competitions.insert_one(new_competition)
        print(f"Created competition with ID: {competition_id}")

        stockNames = request.form.getlist("stockName")
        initialPriceList = request.form.getlist("price")
        
        print(f"Stock names: {stockNames}")
        print(f"Initial prices: {initialPriceList}")

        for i in range(len(stockNames)):
            stock_name = stockNames[i]
            initial_price = float(initialPriceList[i])

            # Add stock name to the database
            new_stock_name = {
                "competition_id": competition_id,
                "name": stock_name,
                "initial_price": initial_price
            }
            stock_name_id = stock_names.insert_one(new_stock_name).inserted_id

            round_prices = request.form.getlist(f"round-{stockNames[i]}")
            print(f"Round prices for {stock_name}: {round_prices}")
            
            for round_number in range(len(round_prices)):
                price = float(round_prices[round_number])

                # Add round to the database
                new_round = {
                    "competition_id": competition_id,
                    "stock_name_id": stock_name_id,
                    "price": price
                }
                rounds.insert_one(new_round)

        print("Successfully created competition and all related data")
        return jsonify({'id': competition_id})
    
    all_competitions = list(competitions.find())
    return render_template("stock_admin.html", competitions=all_competitions)

@app.route("/dashboard", methods=["GET", "POST"])
def receive_data():
    if session.get('logged_in') != True:
            return redirect("/login")
    competitions = list(competitions.find())
    
    latest_competition = competitions[-1] if competitions else None
    if latest_competition:
            ID = latest_competition["_id"]
    else:
            ID = None

    return render_template("dashboard.html", competitions=competitions, ID=ID)

@app.route("/delete-competition", methods=["POST"])
def delete_competition():
    if session.get('logged_in') != True:
            return redirect("/login")
    key_to_delete = request.form.get("keyToDelete")
    competition = competitions.find_one({"_id": int(key_to_delete)})
    if competition:
        competitions.delete_one({"_id": int(key_to_delete)})
    return redirect("/dashboard")

@app.route("/initialBuying/<int:ID>", methods=["GET", "POST"])
def stocksIssue(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    
    # Get the current competition
    current_competition = competitions.find_one({"_id": ID})
    if not current_competition:
        return redirect("/dashboard")

    latest_teams = list(teams.find({"keyCompetition": ID}))
    latest_stocks = list(stock_names.find({"competition_id": ID}))
    currentTeam = None

    if request.method == "POST":
        team = request.form["team"]
        stock = request.form["stock"]
        quantity = request.form["quantity"]
        
        for teamRow in latest_teams:
            if teamRow["teamName"] == team:
                currentTeam = teamRow
                wallet = teamRow["wallet"]
                break
        if currentTeam is None:
            print("Team not found:", team)
            return "Team not found"
                  
        stockPrice = None
        for stockRow in latest_stocks:
            if stockRow["name"] == stock:
                stockPrice = stockRow["initial_price"]
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

        holding_dict = decode_holdings(currentTeam["holding"])
        if stock in holding_dict:
            holding_dict[stock] += int(quantity)
        else:
            holding_dict[stock] = int(quantity)
        currentTeam["holding"] = encode_holdings(holding_dict)
        
        new_stock = {
            "team": team,
            "stock": stock,
            "quantity": quantity,
            "competition_id": ID
        }
        stocks.insert_one(new_stock)

        currentTeam["wallet"] -= totalPrice
        currentTeam["walletTrend"] = f"{currentTeam['wallet']}"

        current_round_prices = {
            stockRow["name"]: stockRow["rounds"][current_competition["currentRound"] - current_competition["numberOfRounds"] - 1]["price"] 
            for stockRow in latest_stocks
        }
        
        for teamRow in latest_teams:               
            holdings = decode_holdings(teamRow["holding"])
            portfolio_worth = 0
            for stock, quantity in holdings.items():
                if stock in current_round_prices:
                    portfolio_worth += quantity * current_round_prices[stock]
            teamRow["portfolioTrend"] = f"{portfolio_worth}"

        teams.update_one({"_id": teamRow["_id"]}, {"$set": teamRow})

        return redirect(url_for("stocksIssue", ID=ID))

    stocks = list(stocks.find({"competition_id": ID}))
    return render_template("initialBuying.html", stocks=stocks, ID=ID, latest_teams=latest_teams, latest_stocks=latest_stocks)

@app.route("/tradingPage/<int:ID>", methods=["GET", "POST"])
def transactions(ID):
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = competitions.find_one({"_id": ID})
    currentRound = latest_competition["currentRound"]

    if latest_competition:
            ID = latest_competition["_id"]
    else:
            ID = None
    
    latest_teams = list(teams.find({"keyCompetition": ID}))
    latest_stocks = list(stock_names.find({"competition_id": ID}))

    if request.method == "POST":
        buyer_team = request.form["buyer_team"]
        seller_team = request.form["seller_team"]
        stock = request.form["stock"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        for teamRow in latest_teams:
            if teamRow["teamName"] == buyer_team:
                buyerTeamObj = teamRow
                buyerWallet = teamRow["wallet"]
            if teamRow["teamName"] == seller_team:
                sellerTeamObj = teamRow
                sellerWallet = teamRow["wallet"]

        total_price = float(quantity) * float(price)

        # Check if the buyer has enough funds
        if total_price > buyerWallet:
            return f"""
            <script>
                alert('Buyer does not have enough funds for this transaction.');
                window.location.href = '/tradingPage/{ID}';
            </script>
            """
        hold = decode_holdings(sellerTeamObj["holding"])

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
        
        holding_dict1 = decode_holdings(buyerTeamObj["holding"])
        if stock in holding_dict1:
            holding_dict1[stock] += int(quantity)
        else:
            holding_dict1[stock] = int(quantity)
        buyerTeamObj["holding"] = encode_holdings(holding_dict1)
        print(buyerTeamObj["holding"])

        holding_dict2 = decode_holdings(sellerTeamObj["holding"])
        if stock in holding_dict2:
            holding_dict2[stock] -= int(quantity)
        else:
            holding_dict2[stock] = int(quantity)
        sellerTeamObj["holding"] = encode_holdings(holding_dict2)
        print(sellerTeamObj["holding"])

        new_transaction = {
            "buyer_team": buyer_team,
            "seller_team": seller_team,
            "stock": stock,
            "quantity": quantity,
            "price": price,
            "roundOfTransaction": currentRound,
            "timeOfTransaction": datetime.utcnow() + timedelta(hours=5, minutes=30)
        }
        transactions.insert_one(new_transaction)

        teams.update_one({"_id": buyerTeamObj["_id"]}, {"$set": {"wallet": buyerTeamObj["wallet"] - total_price}})
        teams.update_one({"_id": sellerTeamObj["_id"]}, {"$set": {"wallet": sellerTeamObj["wallet"] + total_price}})

        return redirect(url_for("transactions", ID = ID))  # Redirect to avoid form resubmission
    transactions = list(transactions.find({"competition_id": ID}).sort("_id", -1))
    return render_template("tradingPage.html", transactions=transactions, ID = ID, teams = latest_teams, latest_stocks = latest_stocks, currentRound = currentRound, user=session.get('user'))

def calculate_portfolio_worth(team, current_round_prices):
    holdings = decode_holdings(team["holding"])
    portfolio_worth = 0
    for stock, quantity in holdings.items():
        if stock in current_round_prices:
            portfolio_worth += quantity * current_round_prices[stock]
    return portfolio_worth

@app.route("/updateNext", methods=["POST"])
def next_round():
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = competitions.find_one({"_id": -1})
    ID = latest_competition["_id"]

    current_round_prices = {
        stockRow["name"]: stockRow["rounds"][latest_competition["currentRound"] - latest_competition["numberOfRounds"] - 1]["price"] for stockRow in stock_names.find({"competition_id": ID})
    }
    print(current_round_prices)

    teams = list(teams.find({"keyCompetition": ID}))
    for team in teams:
        portfolio_worth = calculate_portfolio_worth(team, current_round_prices)
        print(portfolio_worth)
        team["portfolioTrend"] += f",{portfolio_worth}"
        team["walletTrend"] += f",{team['wallet']}"
        print("Portfolio","Team :",team,"-",team["portfolioTrend"])
        print("Wallet Trend","Team :",team,"-",team["walletTrend"])

    # Increment the current round
    competitions.update_one({"_id": ID}, {"$set": {"currentRound": latest_competition["currentRound"] + 1}})

    if latest_competition["currentRound"] > latest_competition["numberOfRounds"]:
        return jsonify({
            "message": "Competition Over",
            "redirect": f"/results/{ID}"
        }), 200
    return jsonify({"message": "Next round started successfully."}), 200

@app.route("/addTeam/<int:ID>", methods=["GET", "POST"])
def addTeam(ID):
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = competitions.find_one({"_id": ID})
    if latest_competition:
            ID = latest_competition["_id"]
    else:
            ID = None
    if request.method == "POST":
        teamName = request.form["teamName"]
        teamMembers = request.form["teamMembers"]
        
        existing_teams = list(teams.find({"keyCompetition": ID}))
        
        for team in existing_teams:
            if team["teamName"] == teamName:
                return f"""
                <script>
                    alert('Team name already exists.');
                    window.location.href = '/addTeam/{ID}';
                </script>
                """
        
        newTeam = {
            "teamName": teamName,
            "teamMembers": teamMembers,
            "keyCompetition": ID
        }
        teams.insert_one(newTeam)
        return redirect(url_for("addTeam", ID=ID))
    
    teams = list(teams.find({"keyCompetition": ID}))
    return render_template("addTeam.html", teams=teams, ID = ID)

@app.route("/removeTeam", methods=["POST"])
def removeTeam():
    if session.get('logged_in') != True:
            return redirect("/login")

    latest_competition = competitions.find_one({"_id": -1})
    if latest_competition:
            ID = latest_competition["_id"]
    else:
            ID = None

    teamID = request.form.get('teamID')
    team = teams.find_one({"_id": int(teamID)})
    if team:
        teams.delete_one({"_id": int(teamID)})
    return redirect(url_for("addTeam", ID=ID))

@app.route("/compOver/<int:ID>")
def compOver(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    latest_competition = competitions.find_one({"_id": -1})
    ID = latest_competition["_id"]
    return render_template("CompOver.html", ID = ID)

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
    latest_competition = competitions.find_one({"_id": -1})
    if latest_competition:
        ID = latest_competition["_id"]
    else:
        ID = None

    latestTeams = list(teams.find({"keyCompetition": ID}))
    names = list(team["teamName"] for team in latestTeams)
    
    portfolio = {}
    cash = {}
    rankings = {}
    netWorth = {}
    numberOfRounds = latest_competition["numberOfRounds"] 

    for name in names:
        for team in latestTeams:
            if team["teamName"] == name:
                portfolio[name] = [0]
                portfolio[name].extend(
                    int(float(value)) for value in team["portfolioTrend"].split(",") if value.strip()
                )  # Skip empty strings
                cash[name] = [latest_competition["walletSize"]]
                cash[name].extend(
                    int(float(value)) for value in team["walletTrend"].split(",") if value.strip()
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
    
    latest_competition = competitions.find_one({"_id": ID})
    if latest_competition:
        ID = latest_competition["_id"]
        rounds = list(range(1, latest_competition["numberOfRounds"] + 1))
    else:
        ID = None
        rounds = []
    
    latestNewsLength = len(list(stock_news.find({"competition_id": ID})))
    print(latestNewsLength)

    if request.method == "POST":
        title = request.form.get("title")
        roundNumber = request.form.get("round")
        content = request.form.get("content")
        image_file = request.files.get('image')  # Use .get() for safety

        # Check if a news event already exists for this round in this competition
        existing_news = stock_news.find_one({"competition_id": ID, "roundNumber": int(roundNumber)})

        image_data = image_file.read() if image_file else None  # Read image data

        if existing_news:
            # Update existing news event
            stock_news.update_one({"_id": existing_news["_id"]}, {"$set": {"title": title, "content": content, "image": image_data}})
            print(f"Updated news for competition {ID}, round {roundNumber}")
        else:
            # Create new news event
            newNews = {
                "title": title,
                "roundNumber": int(roundNumber),
                "content": content,
                "image": image_data,
                "competition_id": ID # Ensure competition_id is set for new entries
            }
            stock_news.insert_one(newNews)
            print(f"Created new news for competition {ID}, round {roundNumber}")

        return redirect(url_for("stockNews", ID=ID))
    

    print("Rendering stock news page.")
    return render_template('stockNews.html', ID=ID, rounds=rounds, numberOfNews = latestNewsLength)

def slides(ID):
    slides = list(stock_news.find({"competition_id": ID}))
    slides_data = {}
    for slide in slides:
        round_number = str(slide["roundNumber"])
        if round_number not in slides_data:
            slides_data[round_number] = []
        img = slide["image"]
        img = base64.b64encode(img).decode('utf-8')
        slides_data[round_number].append({
            "title": slide["title"],
            "content": slide["content"],
            "image": img
        })
    return slides_data

def stock_data(ID):
    stock_data = {}
    stocks = list(stock_names.find({"competition_id": ID}))
    for stock in stocks:
        if stock["name"] not in stock_data:
            stock_data[stock["name"]] = []
        stock_data[stock["name"]].append(stock["initial_price"])
         
    for stock in stocks:
        stockID = stock["_id"]
        stockRound = list(rounds.find({"stock_name_id": stockID}))
        for singleStock in stockRound:
            stock_data[stock["name"]].append(singleStock["price"])
    return stock_data
    

# Updated showNews route
@app.route('/showNews/<int:ID>')
def showNews(ID):
    if session.get('logged_in') != True:
            return redirect("/login")
    
    current_competition = competitions.find_one({"_id": ID})
    if not current_competition:
        # Handle case where competition ID from URL is invalid
        return redirect("/dashboard") # Or an appropriate error page

    round_number = "1"  # Default round
    stock_data_round = get_stock_data_for_round(round_number, ID)
    previous_stock_data = get_stock_data_for_previous_round(round_number, ID)

    return render_template('newsScroll.html', slides=slides(ID), rounds=current_competition["numberOfRounds"], current_round=round_number, stock_data=stock_data_round, ID=ID, total_rounds=current_competition["numberOfRounds"], previous_stock_data=previous_stock_data)

@app.route('/round/<int:ID>/<round_number>')
def round(ID, round_number):
    if session.get('logged_in') != True:
            return redirect("/login")
    
    # Use the ID from the URL directly for competition-specific data
    current_competition = competitions.find_one({"_id": ID}) 
    if not current_competition:
        # Handle case where competition ID from URL is invalid
        return redirect("/dashboard") # Or an appropriate error page

    stock_data_round = get_stock_data_for_round(round_number, ID) # Use the correct ID here
    
    # Debugging: Print slides data before rendering
    all_slides_data = slides(ID) # Use the correct ID here
    print(f"All slides data: {all_slides_data}")
    print(f"Current round: {round_number}")
    if round_number in all_slides_data:
        print(f"Slides for current round ({round_number}): {all_slides_data[round_number]}")
    else:
        print(f"No slides found for current round ({round_number})")

    previous_stock_data = get_stock_data_for_previous_round(round_number, ID)

    return render_template('newsScroll.html', slides=all_slides_data, rounds=all_slides_data.keys(), current_round=round_number, stock_data=stock_data_round, ID =ID, total_rounds=current_competition["numberOfRounds"], previous_stock_data=previous_stock_data)

def get_stock_data_for_round(round_number,ID):
    all_stock_data = stock_data(ID)
    current_round_prices = {}
    for stock, values in all_stock_data.items():
        # Ensure round_number is within the bounds of available data
        if int(round_number) > 0 and int(round_number) <= len(values):
            current_round_prices[stock] = values[int(round_number) - 1]
    return current_round_prices

def get_stock_data_for_previous_round(round_number, ID):
    if int(round_number) > 1:
        previous_round_number = int(round_number) - 1
        return {stock: values[previous_round_number - 1] for stock, values in stock_data(ID).items()}
    return {}

# Add new routes for participant login and dashboard
@app.route("/participant-login", methods=["GET", "POST"])
def participant_login():
    if request.method == "POST":
        team_name = request.form.get("teamName")
        participant_id = request.form.get("participantId")
        
        team = teams.find_one({"teamName": team_name, "participant_id": participant_id})
        
        if team:
            session['participant_logged_in'] = True
            session['team_id'] = team["_id"]
            session['team_name'] = team["teamName"]
            return redirect(url_for('participant_dashboard'))
        else:
            return render_template("participant_login.html", error="Invalid team name or ID")
    
    return render_template("participant_login.html")

@app.route("/participant-dashboard")
def participant_dashboard():
    if not session.get('participant_logged_in'):
        return redirect(url_for('participant_login'))
    
    team = teams.find_one({"_id": session['team_id']})
    if not team:
        session.clear()
        return redirect(url_for('participant_login'))
    
    competition = competitions.find_one({"_id": team["keyCompetition"]})
    
    # Get current portfolio value with robust round access
    current_round_prices = {}
    for stock in competition["stocks"]:
        if len(stock["rounds"]) >= competition["currentRound"]:
            current_round_prices[stock["name"]] = stock["rounds"][competition["currentRound"] - 1]["price"]
        elif stock["rounds"]:
            current_round_prices[stock["name"]] = stock["rounds"][-1]["price"]
        else:
            current_round_prices[stock["name"]] = 0
    portfolio_worth = calculate_portfolio_worth(team, current_round_prices)
    
    # Get holdings
    holdings = decode_holdings(team["holding"])
    
    # Get transaction history
    transactions = list(transactions.find({"$or": [{"buyer_team": team["teamName"]}, {"seller_team": team["teamName"]}]}).sort("timeOfTransaction", -1))
    
    return render_template(
        "participant_dashboard.html",
        team=team,
        competition=competition,
        portfolio_worth=portfolio_worth,
        holdings=holdings,
        transactions=transactions,
        current_round_prices=current_round_prices
    )

@app.route("/participant-logout")
def participant_logout():
    session.pop('participant_logged_in', None)
    session.pop('team_id', None)
    session.pop('team_name', None)
    return redirect(url_for('participant_login'))

with app.app_context():
    pass

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
