"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from dotenv import load_dotenv
load_dotenv()
import os
import random
import string
from datetime import datetime, timedelta, timezone
import time
import base64

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_pymongo import PyMongo
from flask_session import Session
from bson import ObjectId
from pymongo import DESCENDING, IndexModel, ASCENDING
import json
from pymongo.errors import PyMongoError

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGODB_URI", "mongodb://localhost:27017/traders_arena")
app.config['SESSION_TYPE'] = 'mongodb'
app.secret_key = os.getenv("SECRET_KEY", "traders_arena_secret_key")
mongo = PyMongo(app)
server_name = os.getenv("SERVER_NAME")
if server_name:
    app.config["SERVER_NAME"] = server_name
Session(app)

# MongoDB Collection Schemas and Validators
def get_competition_validator():
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["competitionName", "numberOfRounds", "walletSize", "currentRound", "timeOfCreation"],
            "properties": {
                "competitionName": {"bsonType": "string"},
                "numberOfRounds": {"bsonType": "int"},
                "walletSize": {"bsonType": "double"},
                "currentRound": {"bsonType": "int"},
                "timeOfCreation": {"bsonType": "date"}
            }
        }
    }

def get_stock_validator():
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["competition_id", "name", "initial_price"],
            "properties": {
                "competition_id": {"bsonType": "objectId"},
                "name": {"bsonType": "string"},
                "initial_price": {"bsonType": "double"}
            }
        }
    }

def get_team_validator():
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["teamName", "competition_id", "wallet", "participant_id"],
            "properties": {
                "teamName": {"bsonType": "string"},
                "teamMembers": {"bsonType": "string"},
                "competition_id": {"bsonType": "objectId"},
                "wallet": {"bsonType": "double"},
                "walletTrend": {"bsonType": "string", "description": "Comma-separated list of wallet values"},
                "portfolioTrend": {"bsonType": "string", "description": "Comma-separated list of portfolio values"},
                "holding": {"bsonType": "string", "description": "Encoded holdings string"},
                "participant_id": {"bsonType": "string", "minLength": 6, "maxLength": 6}
            }
        }
    }

# Initialize MongoDB collections with schemas and indexes
def init_mongodb():
    try:
        # Create collections with validation
        db = mongo.db

        # Competitions
        if "competitions" not in db.list_collection_names():
            db.create_collection("competitions")
        db.command("collMod", "competitions", validator=get_competition_validator())
        db.competitions.create_index([("competitionName", ASCENDING)], unique=True)
        db.competitions.create_index([("timeOfCreation", DESCENDING)])

        # Stocks
        if "stocks" not in db.list_collection_names():
            db.create_collection("stocks")
        db.command("collMod", "stocks", validator=get_stock_validator())
        db.stocks.create_index([("competition_id", ASCENDING), ("name", ASCENDING)], unique=True)

        # Teams
        if "teams" not in db.list_collection_names():
            db.create_collection("teams")
        db.command("collMod", "teams", validator=get_team_validator())
        db.teams.create_index([("participant_id", ASCENDING)], unique=True)
        db.teams.create_index([("competition_id", ASCENDING), ("teamName", ASCENDING)], unique=True)

        # Rounds
        if "rounds" not in db.list_collection_names():
            db.create_collection("rounds")
        db.rounds.create_index([
            ("competition_id", ASCENDING),
            ("stock_id", ASCENDING),
            ("round_number", ASCENDING)
        ])

        # Transactions
        if "transactions" not in db.list_collection_names():
            db.create_collection("transactions")
        db.transactions.create_index([("competition_id", ASCENDING), ("timeOfTransaction", DESCENDING)])
        db.transactions.create_index([("buyer_team", ASCENDING)])
        db.transactions.create_index([("seller_team", ASCENDING)])

        # Stock Purchases
        if "stock_purchases" not in db.list_collection_names():
            db.create_collection("stock_purchases")
        db.stock_purchases.create_index([("competition_id", ASCENDING)])
        db.stock_purchases.create_index([("team", ASCENDING)])
        db.stock_purchases.create_index([("timeIssued", DESCENDING)])

        # Stock News
        if "stock_news" not in db.list_collection_names():
            db.create_collection("stock_news")
        db.stock_news.create_index([("competition_id", ASCENDING), ("roundNumber", ASCENDING)])

        print("MongoDB initialized successfully with schemas and indexes")
    except PyMongoError as e:
        print(f"Error initializing MongoDB: {e}")
        raise

# Initialize MongoDB on startup
init_mongodb()

def generate_team_id():
    """Generate a random 6-character alphanumeric ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_latest_competition():
    """Get the most recent competition from the database"""
    try:
        return mongo.db.competitions.find_one(
            sort=[("timeOfCreation", DESCENDING)],
            projection={"_id": 1, "competitionName": 1, "currentRound": 1, "numberOfRounds": 1}
        )
    except PyMongoError as e:
        print(f"Error getting latest competition: {e}")
        return None

def get_latest_competition_id():
    """Get the ID of the most recent competition"""
    latest = get_latest_competition()
    return str(latest['_id']) if latest else None

def encode_holdings(holdings_dict):
    """Convert holdings dictionary to string format"""
    return ';'.join(f'{stock}:{quantity}' for stock, quantity in holdings_dict.items())

def decode_holdings(holdings_str):
    """Convert holdings string back to dictionary"""
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

        competition_name = request.form.get("competitionName")
        # Check for duplicate competition name
        existing = mongo.db.competitions.find_one({"competitionName": competition_name})
        if existing:
            return jsonify({'error': 'Competition name already exists. Please choose a different name.'}), 400

        number_of_rounds = int(request.form.get("rounds"))
        wallet_size = float(request.form.get("walletSize"))

        new_competition = {
            "competitionName": competition_name,
            "numberOfRounds": number_of_rounds,
            "walletSize": wallet_size,
            "currentRound": 1,
            "timeOfCreation": datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        }

        competition_id = mongo.db.competitions.insert_one(new_competition).inserted_id
        print(f"Created competition with ID: {competition_id}")

        # Process stocks
        stock_data = []
        stock_names = request.form.getlist("stockName")
        stock_prices = request.form.getlist("price")

        # Create stock documents
        for name, price in zip(stock_names, stock_prices):
            # Get all round prices for this stock
            round_prices = request.form.getlist(f"round-{name}")
            if not round_prices:
                return jsonify({'error': f'Missing round prices for stock {name}'}), 400

            # Create stock document
            stock_doc = {
                "competition_id": competition_id,
                "name": name,
                "initial_price": float(price)
            }
            stock_id = mongo.db.stocks.insert_one(stock_doc).inserted_id

            # Create round documents for this stock
            round_docs = []
            for round_num, price in enumerate(round_prices, 1):
                round_doc = {
                    "competition_id": competition_id,
                    "stock_id": stock_id,
                    "round_number": round_num,
                    "price": float(price)
                }
                round_docs.append(round_doc)

            if round_docs:
                mongo.db.rounds.insert_many(round_docs)

            print(f"Created stock {name} with {len(round_docs)} rounds")

        return jsonify({'id': str(competition_id)})

    competitions = list(mongo.db.competitions.find())
    return render_template("stock_admin.html", competitions=competitions)

@app.route("/dashboard")
def dashboard():
    if session.get('logged_in') != True:
        return redirect("/login")

    competitions = list(mongo.db.competitions.find().sort("timeOfCreation", DESCENDING))
    for comp in competitions:
        comp['_id'] = str(comp['_id'])
        # Get stocks for this competition
        comp['stocks'] = list(mongo.db.stocks.find({"competition_id": ObjectId(comp['_id'])}))
        for stock in comp['stocks']:
            stock['_id'] = str(stock['_id'])
            # Get rounds for this stock
            stock['rounds'] = list(mongo.db.rounds.find({
                "competition_id": ObjectId(comp['_id']),
                "stock_id": ObjectId(stock['_id'])
            }).sort("round_number", ASCENDING))

    return render_template(
        "dashboard.html",
        competitions=competitions
    )

@app.route("/add_team/<competition_id>", methods=["GET", "POST"])
def add_team(competition_id):
    if session.get('logged_in') != True:
        return redirect("/login")

    if request.method == "POST":
        competition = mongo.db.competitions.find_one({"_id": ObjectId(competition_id)})
        if not competition:
            return "Competition not found", 404

        new_team = {
            "teamName": request.form.get("teamName"),
            "teamMembers": request.form.get("teamMembers"),
            "competition_id": ObjectId(competition_id),
            "wallet": competition["walletSize"],
            "walletTrend": "",
            "portfolioTrend": "",
            "holding": "",
            "participant_id": generate_team_id()
        }

        mongo.db.teams.insert_one(new_team)
        return redirect(f"/add_team/{competition_id}")

    # Get the teams for this competition
    teams = list(mongo.db.teams.find({"competition_id": ObjectId(competition_id)}))
    for team in teams:
        team['_id'] = str(team['_id'])

    return render_template("addTeam.html", teams=teams, ID=competition_id)

@app.route("/api/update_round/<competition_id>", methods=["POST"])
def update_round(competition_id):
    if session.get('logged_in') != True:
        return jsonify({"error": "Unauthorized"}), 401

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Start a MongoDB transaction
            with mongo.db.client.start_session() as session:
                with session.start_transaction():
                    competition = mongo.db.competitions.find_one(
                    {"_id": ObjectId(competition_id)},
                    session=session
                )
                if not competition:
                    return jsonify({"error": "Competition not found"}), 404

                current_round = competition["currentRound"]
                number_of_rounds = competition["numberOfRounds"]

                if current_round >= number_of_rounds:
                    return jsonify({"error": "Competition already completed"}), 400

                # Validate and update round prices
                stocks = request.json.get("stocks", [])
                if not stocks:
                    return jsonify({"error": "No stock prices provided"}), 400

                round_docs = []
                for stock in stocks:
                    try:
                        stock_id = ObjectId(stock["id"])
                        price = float(stock["price"])
                        if price < 0:
                            return jsonify({"error": f"Invalid price for stock {stock['id']}"}), 400

                        round_doc = {
                            "competition_id": ObjectId(competition_id),
                            "stock_id": stock_id,
                            "price": price,
                            "round_number": current_round + 1,
                            "timestamp": datetime.now(timezone.utc)
                        }
                        round_docs.append(round_doc)
                    except (KeyError, ValueError) as e:
                        return jsonify({"error": f"Invalid stock data: {str(e)}"}), 400

                # Insert round prices
                if round_docs:
                    mongo.db.rounds.insert_many(round_docs, session=session)

                # Update teams' portfolio and wallet trends
                teams = mongo.db.teams.find(
                    {"competition_id": ObjectId(competition_id)},
                    session=session
                )

                current_prices = {
                    str(doc["stock_id"]): doc["price"]
                    for doc in round_docs
                }

                for team in teams:
                    holdings = decode_holdings(team.get("holding", ""))
                    portfolio_worth = sum(
                        quantity * current_prices.get(stock, 0)
                        for stock, quantity in holdings.items()
                    )

                    mongo.db.teams.update_one(
                        {"_id": team["_id"]},
                        {
                            "$set": {
                                "portfolioTrend": team.get("portfolioTrend", "") + f",{portfolio_worth}",
                                "walletTrend": team.get("walletTrend", "") + f",{team['wallet']}"
                            }
                        },
                        session=session
                    )

                # Update competition round
                mongo.db.competitions.update_one(
                    {"_id": ObjectId(competition_id)},
                    {
                        "$inc": {"currentRound": 1},
                        "$set": {"lastUpdated": datetime.now(datetime.UTC)}
                    },
                    session=session
                )

                if current_round + 1 >= number_of_rounds:
                    return jsonify({
                        "success": True,
                        "message": "Competition completed",
                        "redirect": f"/results/{competition_id}"
                    })

                    return jsonify({"success": True})

        except PyMongoError as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"Database error in update_round after {max_retries} retries: {e}")
                return jsonify({"error": "Database error occurred"}), 500
            print(f"Retrying round update (attempt {retry_count + 1})")
            time.sleep(0.5 * retry_count)  # Exponential backoff
        except Exception as e:
            print(f"Unexpected error in update_round: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/stockNews/<competition_id>', methods=["GET", "POST"])
def stockNews(competition_id):
    if session.get('logged_in') != True:
        return redirect("/login")

    try:
        try:
            try:
                competition = mongo.db.competitions.find_one({"_id": ObjectId(competition_id)})
            except:
                return redirect("/dashboard")
        except:
            return redirect("/dashboard")
        if not competition:
            return "Competition not found", 404

        rounds = list(range(1, competition["numberOfRounds"] + 1))
        news_count = mongo.db.stock_news.count_documents({"competition_id": ObjectId(competition_id)})

        if request.method == "POST":
            title = request.form.get("title")
            round_number = int(request.form.get("round"))
            content = request.form.get("content")
            image_data = None

            if 'image' in request.files:
                image_data = request.files['image'].read()

            # Check if news already exists for this round
            existing_news = mongo.db.stock_news.find_one({
                "competition_id": ObjectId(competition_id),
                "roundNumber": round_number
            })

            if existing_news:
                # Update existing news
                update_data = {
                    "title": title,
                    "content": content
                }
                if image_data:
                    update_data["image"] = image_data

                mongo.db.stock_news.update_one(
                    {"_id": existing_news["_id"]},
                    {"$set": update_data}
                )
                print(f"Updated news for competition {competition_id}, round {round_number}")
                flash(f"Successfully updated news for round {round_number}", "success")
            else:
                # Create new news
                new_news = {
                    "competition_id": ObjectId(competition_id),
                    "title": title,
                    "roundNumber": round_number,
                    "content": content,
                    "image": image_data,
                    "timestamp": datetime.now(timezone.utc)
                }
                mongo.db.stock_news.insert_one(new_news)
                print(f"Created new news for competition {competition_id}, round {round_number}")
                flash(f"Successfully added new news for round {round_number}", "success")

            # Stay on the same page after adding news
            return redirect(url_for("stockNews", competition_id=competition_id))

        return render_template(
            'stockNews.html',
            ID=competition_id,
            rounds=rounds,
            numberOfNews=news_count
        )

    except PyMongoError as e:
        print(f"Database error in stockNews: {e}")
        flash(f"Database error: {str(e)}", "error")
        return redirect(url_for("stockNews", competition_id=competition_id))
    except Exception as e:
        print(f"Unexpected error in stockNews: {e}")
        flash(f"An unexpected error occurred", "error")
        return redirect(url_for("stockNews", competition_id=competition_id))

@app.route("/api/add_news", methods=["POST"])
def add_news():
    if session.get('logged_in') != True:
        return jsonify({"error": "Unauthorized"}), 401

    competition_id = request.form.get("competition_id")
    if not competition_id:
        return jsonify({"error": "Competition ID required"}), 400

    news_doc = {
        "competition_id": ObjectId(competition_id),
        "title": request.form.get("title"),
        "content": request.form.get("content"),
        "roundNumber": int(request.form.get("roundNumber")),
        "image": request.files["image"].read() if "image" in request.files else None,
        "timestamp": datetime.now(timezone.utc)
    }

    mongo.db.stock_news.insert_one(news_doc)
    return jsonify({"success": True})

@app.route("/participant-login", methods=["GET", "POST"])
def participant_login():
    if request.method == "POST":
        team_name = request.form.get("teamName")
        participant_id = request.form.get("participantId")

        team = mongo.db.teams.find_one({
            "teamName": team_name,
            "participant_id": participant_id
        })

        if team:
            session['participant_logged_in'] = True
            session['team_id'] = str(team['_id'])
            session['team_name'] = team['teamName']
            return redirect("/participant-dashboard")
        else:
            return render_template("participant_login.html", error="Invalid team name or ID")

    return render_template("participant_login.html")

@app.route("/participant_login", methods=["GET", "POST"])
def participant_login_redirect():
    # Backward compatibility route
    return redirect("/participant-login")

@app.route("/participant-dashboard")
def participant_dashboard():
    if not session.get('participant_logged_in'):
        return redirect("/participant-login")

    team_id = session.get('team_id')
    if not team_id:
        session.clear()
        return redirect("/participant-login")

    try:
        team = mongo.db.teams.find_one({"_id": ObjectId(team_id)})
        if not team:
            session.clear()
            return redirect("/participant-login")

        competition = mongo.db.competitions.find_one({"_id": team['competition_id']})
        if not competition:
            return render_template("participant_dashboard.html", error="Competition not found")

        # Get current stock prices
        stocks = list(mongo.db.stocks.find({"competition_id": team['competition_id']}))
        for stock in stocks:
            stock['_id'] = str(stock['_id'])

        # Get current round prices
        current_round = competition['currentRound']
        current_prices = {}
        for stock in stocks:
            round_doc = mongo.db.rounds.find_one({
                "competition_id": team['competition_id'],
                "stock_id": ObjectId(stock['_id']),
                "round_number": current_round - 1  # -1 because rounds are 0-indexed in data
            })
            if round_doc:
                current_prices[stock['name']] = round_doc['price']
            else:
                current_prices[stock['name']] = stock['initial_price']

        # Calculate portfolio worth
        holdings = decode_holdings(team.get('holding', ''))
        portfolio_worth = sum(
            quantity * current_prices.get(stock, 0)
            for stock, quantity in holdings.items()
        )

        # Get transaction history
        transactions = list(mongo.db.transactions.find({
            "$or": [
                {"buyer_team": team['teamName']},
                {"seller_team": team['teamName']}
            ],
            "competition_id": team['competition_id']
        }).sort("timeOfTransaction", DESCENDING))

        # Convert ObjectId instances to strings for template
        for transaction in transactions:
            if '_id' in transaction:
                transaction['_id'] = str(transaction['_id'])

        # Check if competition is over
        competition_over = competition.get('completed', False) or competition['currentRound'] > competition['numberOfRounds']

        return render_template(
            "participant_dashboard.html",
            team=team,
            competition=competition,
            stocks=stocks,
            portfolio_worth=portfolio_worth,
            holdings=holdings,
            transactions=transactions,
            current_prices=current_prices,
            competition_over=competition_over
        )
    except Exception as e:
        print(f"Error in participant dashboard: {e}")
        return render_template("participant_dashboard.html", error=f"An error occurred: {str(e)}")

@app.route("/participant_dashboard")
def participant_dashboard_redirect():
    # Backward compatibility route
    return redirect("/participant-dashboard")

@app.route("/api/trade", methods=["POST"])
def trade():
    if 'team_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Start a MongoDB transaction
            with mongo.db.client.start_session() as session:
                with session.start_transaction():
                    # Get team data
                    team = mongo.db.teams.find_one(
                    {"_id": ObjectId(session['team_id'])},
                    session=session
                )
                if not team:
                    return jsonify({"error": "Team not found"}), 404

                # Validate transaction data
                try:
                    buyer_team = request.json["buyer_team"]
                    seller_team = request.json["seller_team"]
                    stock_name = request.json["stock"]
                    quantity = int(request.json["quantity"])
                    price = float(request.json["price"])
                    round_num = int(request.json["round"])
                except (KeyError, ValueError) as e:
                    return jsonify({"error": f"Invalid transaction data: {str(e)}"}), 400

                # Get buyer and seller data
                buyer = mongo.db.teams.find_one(
                    {"teamName": buyer_team, "competition_id": team['competition_id']},
                    session=session
                )
                seller = mongo.db.teams.find_one(
                    {"teamName": seller_team, "competition_id": team['competition_id']},
                    session=session
                )

                if not buyer or not seller:
                    return jsonify({"error": "Buyer or seller not found"}), 404

                total_amount = price * quantity

                # Validate buyer has enough funds
                if buyer["wallet"] < total_amount:
                    return jsonify({"error": "Insufficient funds"}), 400

                # Validate seller has enough stocks
                seller_holdings = decode_holdings(seller.get("holding", ""))
                if seller_holdings.get(stock_name, 0) < quantity:
                    return jsonify({"error": "Insufficient stocks"}), 400

                # Create transaction record
                transaction = {
                    "buyer_team": buyer_team,
                    "seller_team": seller_team,
                    "competition_id": team['competition_id'],
                    "roundOfTransaction": round_num,
                    "stock": stock_name,
                    "quantity": quantity,
                    "price": price,
                    "timeOfTransaction": datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
                }

                mongo.db.transactions.insert_one(transaction, session=session)

                # Update buyer holdings and wallet
                buyer_holdings = decode_holdings(buyer.get("holding", ""))
                buyer_holdings[stock_name] = buyer_holdings.get(stock_name, 0) + quantity

                mongo.db.teams.update_one(
                    {"_id": buyer["_id"]},
                    {
                        "$set": {
                            "holding": encode_holdings(buyer_holdings),
                            "walletTrend": buyer["walletTrend"] + f",{buyer['wallet'] - total_amount}"
                        },
                        "$inc": {"wallet": -total_amount}
                    },
                    session=session
                )

                # Update seller holdings and wallet
                seller_holdings[stock_name] -= quantity
                if seller_holdings[stock_name] == 0:
                    del seller_holdings[stock_name]

                mongo.db.teams.update_one(
                    {"_id": seller["_id"]},
                    {
                        "$set": {
                            "holding": encode_holdings(seller_holdings),
                            "walletTrend": seller["walletTrend"] + f",{seller['wallet'] + total_amount}"
                        },
                        "$inc": {"wallet": total_amount}
                    },
                    session=session
                )

                # Update portfolio trends
                competition = mongo.db.competitions.find_one(
                    {"_id": team['competition_id']},
                    session=session
                )

                if competition:
                        current_round = competition["currentRound"]
                        # Get current prices for all stocks in this competition
                        current_prices = {}
                        stocks = mongo.db.stocks.find(
                            {"competition_id": team['competition_id']},
                            session=session
                        )

                        for stock in stocks:
                            price_doc = mongo.db.rounds.find_one(
                                {
                                    "competition_id": team['competition_id'],
                                    "stock_id": stock["_id"],
                                    "round_number": current_round
                                },
                                session=session
                            )
                            if price_doc:
                                current_prices[stock["name"]] = price_doc["price"]

                        # Update portfolio trends for both teams
                        for team_doc in [buyer, seller]:
                            holdings = decode_holdings(team_doc.get("holding", ""))
                            portfolio_worth = sum(
                                quantity * current_prices.get(stock, 0)
                                for stock, quantity in holdings.items()
                            )
                            mongo.db.teams.update_one(
                                {"_id": team_doc["_id"]},
                                {"$set": {"portfolioTrend": team_doc.get("portfolioTrend", "") + f",{portfolio_worth}"}},
                                session=session
                            )

                return jsonify({"success": True})

        except PyMongoError as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"Database error in trade after {max_retries} retries: {e}")
                return jsonify({"error": "Database error occurred"}), 500
            print(f"Retrying transaction (attempt {retry_count + 1})")
            time.sleep(0.5 * retry_count)  # Exponential backoff
        except Exception as e:
            print(f"Unexpected error in trade: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/showNews/<competition_id>')
def showNews(competition_id):
    if session.get('logged_in') != True:
        return redirect("/login")

    try:
        # Convert string ID to ObjectId safely
        try:
            competition_obj_id = ObjectId(competition_id)
        except:
            flash("Invalid competition ID format", "error")
            return redirect("/dashboard")

        competition = mongo.db.competitions.find_one({"_id": competition_obj_id})
        if not competition:
            flash("Competition not found", "error")
            return redirect("/dashboard")

        # Get round from query parameter or default to first round
        round_number = request.args.get('round', "1")
        rounds = competition["numberOfRounds"]

        # Get news slides
        slides_data = {}
        all_news = mongo.db.stock_news.find({"competition_id": competition_obj_id})

        for news in all_news:
            round_num = str(news["roundNumber"])
            if round_num not in slides_data:
                slides_data[round_num] = []

            image_b64 = None
            if news.get("image"):
                image_b64 = base64.b64encode(news["image"]).decode('utf-8')

            slides_data[round_num].append({
                "title": news["title"],
                "content": news["content"],
                "image": image_b64
            })

        # Get stock data for current round
        stock_data_round = get_stock_data_for_round(round_number, competition_id)
        previous_stock_data = get_stock_data_for_previous_round(round_number, competition_id)

        return render_template(
            'newsScroll.html',
            slides=slides_data,
            rounds=slides_data.keys(),
            current_round=round_number,
            stock_data=stock_data_round,
            ID=competition_id,
            competition_id=competition_id,
            total_rounds=rounds,
            previous_stock_data=previous_stock_data
        )

    except Exception as e:
        print(f"Error in showNews: {e}")
        flash(f"An error occurred: {str(e)}", "error")
        return redirect("/dashboard")

@app.route("/delete-competition", methods=["POST"])
def delete_competition():
    if session.get('logged_in') != True:
        return redirect("/login")

    competition_id = request.form.get("keyToDelete")
    try:
        # Delete all related data
        mongo.db.stocks.delete_many({"competition_id": ObjectId(competition_id)})
        mongo.db.rounds.delete_many({"competition_id": ObjectId(competition_id)})
        mongo.db.teams.delete_many({"competition_id": ObjectId(competition_id)})
        mongo.db.transactions.delete_many({"competition_id": ObjectId(competition_id)})
        mongo.db.stock_news.delete_many({"competition_id": ObjectId(competition_id)})

        # Delete the competition itself
        mongo.db.competitions.delete_one({"_id": ObjectId(competition_id)})

        return redirect("/dashboard")
    except Exception as e:
        print(f"Error deleting competition: {e}")
        return redirect("/dashboard")

@app.route("/removeTeam", methods=["POST"])
def removeTeam():
    if session.get('logged_in') != True:
        return redirect("/login")

    team_id = request.form.get("teamID")
    if not team_id:
        return jsonify({"error": "Team ID is required"}), 400

    try:
        # Get the team to find its competition
        team = mongo.db.teams.find_one({"_id": ObjectId(team_id)})
        if not team:
            return jsonify({"error": "Team not found"}), 404

        competition_id = team.get("competition_id")
        competition_id_str = str(competition_id)

        # Delete the team
        result = mongo.db.teams.delete_one({"_id": ObjectId(team_id)})

        if result.deleted_count == 0:
            return jsonify({"error": "Failed to delete team"}), 500

        # Redirect back to add team page with the same competition
        if competition_id:
            return redirect(f"/add_team/{competition_id_str}")
        else:
            return redirect("/dashboard")
    except Exception as e:
        print(f"Error removing team: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/round/<competition_id>/<round_number>')
def round_view(competition_id, round_number):
    # Redirect to showNews with round parameter in query string
    return redirect(f"/showNews/{competition_id}?round={round_number}")

def get_stock_data_for_round(round_number, competition_id):
    """Get stock prices for a specific round"""
    try:
        round_num = int(round_number)
        try:
            competition_obj_id = ObjectId(competition_id)
            stocks = mongo.db.stocks.find({"competition_id": competition_obj_id})
        except Exception as e:
            print(f"Error finding stocks: {e}")
            return {}

        stock_prices = {}
        for stock in stocks:
            # For round 1, use initial price
            if round_num == 1:
                stock_prices[stock["name"]] = stock["initial_price"]
            else:
                # For other rounds, get price from rounds collection
                try:
                    round_data = mongo.db.rounds.find_one({
                        "competition_id": competition_obj_id,
                        "stock_id": stock["_id"],
                        "round_number": round_num - 1  # -1 because we store next round's prices
                    })
                    if round_data:
                        stock_prices[stock["name"]] = round_data["price"]
                    else:
                        # Fallback to initial price if round data not found
                        stock_prices[stock["name"]] = stock["initial_price"]
                except Exception as e:
                    print(f"Error getting round data for stock {stock['name']}: {e}")
                    stock_prices[stock["name"]] = stock["initial_price"]

        return stock_prices
    except Exception as e:
        print(f"Error getting stock data for round {round_number}: {e}")
        return {}

def get_stock_data_for_previous_round(round_number, competition_id):
    """Get stock prices for the previous round"""
    try:
        round_num = int(round_number)
        if round_num <= 1:
            return {}

        return get_stock_data_for_round(str(round_num - 1), competition_id)
    except Exception as e:
        print(f"Error getting previous stock data: {e}")
        return {}

@app.route("/results/<competition_id>", methods=["GET"])
def results(competition_id):
    if session.get('logged_in') != True:
        return redirect("/login")

    try:
        print(f"Results page accessed for competition: {competition_id}")

        try:
            competition = mongo.db.competitions.find_one({"_id": ObjectId(competition_id)})
        except Exception as e:
            print(f"Error converting competition ID to ObjectId: {e}")
            flash("Invalid competition ID format", "error")
            return redirect("/dashboard")

        if not competition:
            print(f"Competition not found with ID: {competition_id}")
            flash("Competition not found", "error")
            return redirect("/dashboard")

        print(f"Found competition: {competition.get('competitionName')}")

        # Check if competition is actually over before showing results
        # Allow access if coming from completion redirect or if competition is marked as completed
        completed_param = request.args.get('completed')
        is_completed = competition.get("completed", False)
        current_round = competition.get("currentRound", 0)
        number_of_rounds = competition.get("numberOfRounds", 0)

        if not completed_param and not is_completed and current_round <= number_of_rounds:
            print(f"Competition is still ongoing. Current round: {current_round}, Total rounds: {number_of_rounds}")
            flash("Competition is still ongoing. Results will be available after all rounds are completed.", "warning")
            return redirect(f"/tradingPage/{competition_id}")
        teams = list(mongo.db.teams.find({"competition_id": ObjectId(competition_id)}))
        print(f"Found {len(teams)} teams for this competition")

        portfolio = {}
        cash = {}
        rankings = {}
        netWorth = {}
        numberOfRounds = competition["numberOfRounds"]

        for team in teams:
            name = team["teamName"]
            portfolio[name] = [0]
            if team.get("portfolioTrend"):
                portfolio[name].extend(
                    int(float(value)) for value in team["portfolioTrend"].split(",") if value.strip()
                )

            cash[name] = [competition["walletSize"]]
            if team.get("walletTrend"):
                cash[name].extend(
                    int(float(value)) for value in team["walletTrend"].split(",") if value.strip()
                )

            if portfolio[name] and cash[name]:
                netWorth[name] = [cash[name][-1] + portfolio[name][-1]]

        # Sort teams by net worth
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
            netWorth=netWorth,
            ID=competition_id,
            competition=competition
        )
    except Exception as e:
        print(f"Error in results: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash(f"An error occurred: {str(e)}", "error")
        return render_template(
            "results.html",
            portfolio={},
            cash={},
            rankings={},
            numberOfRounds=0,
            netWorth={},
            ID=competition_id,
            error=str(e)
        )

@app.route("/tradingPage/<competition_id>", methods=["GET", "POST"])
@app.route("/trading_page/<competition_id>", methods=["GET", "POST"])
def transactions(competition_id):
    if session.get('logged_in') != True:
        return redirect("/login")

    try:
        print(f"Trading page accessed for competition: {competition_id}")

        # Safely convert string ID to ObjectId
        try:
            competition_obj_id = ObjectId(competition_id)
        except Exception as e:
            print(f"Error converting competition ID to ObjectId: {e}")
            flash("Invalid competition ID format", "error")
            return redirect("/dashboard")

        competition = mongo.db.competitions.find_one({"_id": competition_obj_id})
        if not competition:
            print(f"Competition not found with ID: {competition_id}")
            flash("Competition not found", "error")
            return redirect("/dashboard")

        print(f"Competition found: {competition.get('competitionName', 'Unknown')}")
        currentRound = competition["currentRound"]

        teams = list(mongo.db.teams.find({"competition_id": competition_obj_id}))
        print(f"Found {len(teams)} teams for this competition")
        for team in teams:
            team['_id'] = str(team['_id'])

        stocks = list(mongo.db.stocks.find({"competition_id": competition_obj_id}))
        print(f"Found {len(stocks)} stocks for this competition")
        for stock in stocks:
            stock['_id'] = str(stock['_id'])

        if request.method == "POST":
            buyer_team = request.form["buyer_team"]
            seller_team = request.form["seller_team"]
            stock = request.form["stock"]
            quantity = int(request.form["quantity"])
            price = float(request.form["price"])

            # Find buyer and seller teams
            buyer = None
            seller = None
            for team in teams:
                if team["teamName"] == buyer_team:
                    buyer = team
                if team["teamName"] == seller_team:
                    seller = team

            if not buyer or not seller:
                return f"""
                <script>
                    alert('Team not found.');
                    window.location.href = '/tradingPage/{competition_id}';
                </script>
                """

            total_price = quantity * price

            # Check if buyer has enough funds
            if total_price > buyer["wallet"]:
                return f"""
                <script>
                    alert('Buyer does not have enough funds for this transaction.');
                    window.location.href = '/tradingPage/{competition_id}';
                </script>
                """

            # Check if seller has enough stock
            seller_holdings = decode_holdings(seller.get("holding", ""))
            if stock not in seller_holdings or seller_holdings[stock] < quantity:
                return f"""
                <script>
                    alert('Seller does not have enough stock for this transaction.');
                    window.location.href = '/tradingPage/{competition_id}';
                </script>
                """

            # Update buyer holdings
            buyer_holdings = decode_holdings(buyer.get("holding", ""))
            buyer_holdings[stock] = buyer_holdings.get(stock, 0) + quantity

            # Update seller holdings
            seller_holdings[stock] -= quantity
            if seller_holdings[stock] == 0:
                del seller_holdings[stock]

            # Create transaction record
            transaction = {
                "buyer_team": buyer_team,
                "seller_team": seller_team,
                "competition_id": ObjectId(competition_id),
                "roundOfTransaction": currentRound,
                "stock": stock,
                "quantity": quantity,
                "price": price,
                "timeOfTransaction": datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
            }

            # Update database
            mongo.db.transactions.insert_one(transaction)

            # Update buyer
            mongo.db.teams.update_one(
                {"_id": ObjectId(buyer["_id"])},
                {
                    "$set": {"holding": encode_holdings(buyer_holdings)},
                    "$inc": {"wallet": -total_price}
                }
            )

            # Update seller
            mongo.db.teams.update_one(
                {"_id": ObjectId(seller["_id"])},
                {
                    "$set": {"holding": encode_holdings(seller_holdings)},
                    "$inc": {"wallet": total_price}
                }
            )

            # Use a direct URL to avoid URL generation issues
            return redirect(f"/tradingPage/{competition_id}")

        # Get all transactions for this competition
        try:
            # Ensure collection exists before querying
            if "transactions" in mongo.db.list_collection_names():
                transactions_list = list(mongo.db.transactions.find(
                    {"competition_id": competition_obj_id}
                ).sort("timeOfTransaction", DESCENDING))
                print(f"Found {len(transactions_list)} transactions")
            else:
                print("transactions collection doesn't exist")
                transactions_list = []
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            transactions_list = []

        return render_template(
            "tradingPage.html",
            transactions=transactions_list,
            ID=competition_id,
            teams=teams,
            latest_stocks=stocks,
            currentRound=currentRound,
            numberOfRounds=competition["numberOfRounds"],
            user=session.get('user')
        )
    except Exception as e:
        print(f"Error in trading page: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash(f"An error occurred: {str(e)}", "error")
        # Render the template with error instead of redirecting
        return render_template(
            "tradingPage.html",
            transactions=[],
            ID=competition_id,
            teams=[],
            latest_stocks=[],
            currentRound=1,
            numberOfRounds=0,
            user=session.get('user'),
            error=str(e)
        )

@app.route("/initialBuying/<competition_id>", methods=["GET", "POST"])
@app.route("/initial_buying/<competition_id>", methods=["GET", "POST"])
def stocksIssue(competition_id):
    print(f"stocksIssue route called with competition_id: {competition_id}")
    if session.get('logged_in') != True:
        return redirect("/login")

    # Make sure the stock_purchases collection exists
    if "stock_purchases" not in mongo.db.list_collection_names():
        try:
            mongo.db.create_collection("stock_purchases")
            mongo.db.stock_purchases.create_index([("competition_id", ASCENDING)])
            mongo.db.stock_purchases.create_index([("team", ASCENDING)])
            mongo.db.stock_purchases.create_index([("timeIssued", DESCENDING)])
            print("Created stock_purchases collection")
        except Exception as e:
            print(f"Error creating stock_purchases collection: {e}")

    try:
        print(f"Initial buying route accessed for competition: {competition_id}")

        try:
            competition = mongo.db.competitions.find_one({"_id": ObjectId(competition_id)})
        except Exception as e:
            print(f"Error converting competition ID to ObjectId: {e}")
            flash("Invalid competition ID format", "error")
            return redirect("/dashboard")

        if not competition:
            print(f"Competition not found with ID: {competition_id}")
            flash("Competition not found", "error")
            return redirect("/dashboard")

        print(f"Competition found: {competition.get('competitionName', 'Unknown')}")

        teams = list(mongo.db.teams.find({"competition_id": ObjectId(competition_id)}))
        print(f"Found {len(teams)} teams for this competition")
        for team in teams:
            team['_id'] = str(team['_id'])

        stocks = list(mongo.db.stocks.find({"competition_id": ObjectId(competition_id)}))
        print(f"Found {len(stocks)} stocks for this competition")
        for stock in stocks:
            stock['_id'] = str(stock['_id'])

        if request.method == "POST":
            team_name = request.form["team"]
            stock_name = request.form["stock"]
            quantity = int(request.form["quantity"])

            # Find the team and stock
            team_doc = None
            for team in teams:
                if team["teamName"] == team_name:
                    team_doc = team
                    break

            if not team_doc:
                return "Team not found"

            stock_doc = None
            for stock in stocks:
                if stock["name"] == stock_name:
                    stock_doc = stock
                    break

            if not stock_doc:
                return "Stock not found"

            # Calculate total price
            total_price = quantity * stock_doc["initial_price"]

            # Check if team has enough funds
            if team_doc["wallet"] < total_price:
                return f"""
                <script>
                    alert('Team does not have enough funds for this purchase.');
                    window.location.href = '/initialBuying/{competition_id}';
                </script>
                """

            # Update team holdings
            holdings = decode_holdings(team_doc.get("holding", ""))
            holdings[stock_name] = holdings.get(stock_name, 0) + quantity

            # Update database
            mongo.db.teams.update_one(
                {"_id": ObjectId(team_doc["_id"])},
                {
                    "$set": {
                        "holding": encode_holdings(holdings),
                        "walletTrend": team_doc.get("walletTrend", "") + f",{team_doc['wallet'] - total_price}"
                    },
                    "$inc": {"wallet": -total_price}
                }
            )

            # Record the stock purchase
            purchase = {
                "team": team_name,
                "stock": stock_name,
                "quantity": quantity,
                "competition_id": ObjectId(competition_id),
                "timeIssued": datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
            }

            try:
                # Ensure collection exists before inserting
                if "stock_purchases" not in mongo.db.list_collection_names():
                    mongo.db.create_collection("stock_purchases")
                    mongo.db.stock_purchases.create_index([("competition_id", ASCENDING)])
                    mongo.db.stock_purchases.create_index([("team", ASCENDING)])
                    print("Created stock_purchases collection on demand")

                mongo.db.stock_purchases.insert_one(purchase)
            except Exception as e:
                print(f"Error recording stock purchase: {e}")
                print(f"Error type: {type(e)}")
                import traceback
                traceback.print_exc()

            # Update portfolio trend
            portfolio_worth = sum(
                holdings.get(s["name"], 0) * s["initial_price"]
                for s in stocks
            )

            mongo.db.teams.update_one(
                {"_id": ObjectId(team_doc["_id"])},
                {"$set": {"portfolioTrend": team_doc.get("portfolioTrend", "") + f",{portfolio_worth}"}}
            )

            # Use a direct URL to avoid URL generation issues
            return redirect(f"/initialBuying/{competition_id}")

        # Get all stock purchases for this competition
        try:
            # Ensure collection exists before querying
            if "stock_purchases" in mongo.db.list_collection_names():
                purchases = list(mongo.db.stock_purchases.find(
                    {"competition_id": ObjectId(competition_id)}
                ).sort("timeIssued", DESCENDING))
            else:
                print("stock_purchases collection doesn't exist")
                purchases = []
        except Exception as e:
            print(f"Error fetching stock purchases: {e}")
            purchases = []

        return render_template(
            "initialBuying.html",
            stocks=purchases,
            ID=competition_id,
            latest_teams=teams,
            latest_stocks=stocks
        )
    except Exception as e:
        print(f"Error in initial buying: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash(f"An error occurred: {str(e)}", "error")
        return render_template(
            "initialBuying.html",
            stocks=[],
            ID=competition_id,
            latest_teams=[],
            latest_stocks=[],
            error=str(e)
        )

@app.route("/completeCompetition", methods=["POST"])
def complete_competition():
    if session.get('logged_in') != True:
        return redirect("/login")

    try:
        competition_id = request.form.get("competition_id") or request.json.get("competition_id")
        if not competition_id:
            print("No competition_id provided in request")
            flash("Competition ID required", "error")
            return redirect("/dashboard")

        print(f"Completing competition: {competition_id}")

        try:
            competition_obj_id = ObjectId(competition_id)
            competition = mongo.db.competitions.find_one({"_id": competition_obj_id})
        except Exception as e:
            print(f"Error converting competition ID to ObjectId: {e}")
            flash(f"Invalid competition ID format: {str(e)}", "error")
            return redirect("/dashboard")

        if not competition:
            print(f"Competition not found with ID: {competition_id}")
            flash("Competition not found", "error")
            return redirect("/dashboard")

        current_round = competition["currentRound"]
        number_of_rounds = competition["numberOfRounds"]

        # Only allow completion if we're on the final round
        if current_round != number_of_rounds:
            print(f"Cannot complete competition. Current round: {current_round}, Total rounds: {number_of_rounds}")
            flash("Competition can only be completed during the final round.", "error")
            return redirect(f"/tradingPage/{competition_id}")

        # Update team trends for the final time
        try:
            # Get current stock prices for the final round
            stocks = list(mongo.db.stocks.find({"competition_id": competition_obj_id}))
            current_prices = {}
            for stock in stocks:
                stock_id = stock["_id"]
                try:
                    round_price = mongo.db.rounds.find_one({
                        "competition_id": competition_obj_id,
                        "stock_id": stock_id,
                        "round_number": current_round
                    })
                    if round_price:
                        current_prices[stock["name"]] = round_price["price"]
                    else:
                        current_prices[stock["name"]] = stock["initial_price"]
                except Exception as e:
                    print(f"Error getting final round price for stock {stock['name']}: {e}")
                    current_prices[stock["name"]] = stock["initial_price"]

            # Update final team trends
            teams = list(mongo.db.teams.find({"competition_id": competition_obj_id}))
            for team in teams:
                team_id = team["_id"]
                team_name = team.get("teamName", "Unknown")

                try:
                    holdings = decode_holdings(team.get("holding", ""))
                    wallet = team.get("wallet", 0)

                    portfolio_worth = sum(
                        quantity * current_prices.get(stock, 0)
                        for stock, quantity in holdings.items()
                    )

                    current_portfolio_trend = team.get("portfolioTrend", "")
                    current_wallet_trend = team.get("walletTrend", "")

                    new_portfolio_trend = f"{current_portfolio_trend},{portfolio_worth}" if current_portfolio_trend else f"{portfolio_worth}"
                    new_wallet_trend = f"{current_wallet_trend},{wallet}" if current_wallet_trend else f"{wallet}"

                    print(f"Final update for team {team_name}: Portfolio worth: {portfolio_worth}, Wallet: {wallet}")

                    mongo.db.teams.update_one(
                        {"_id": team_id},
                        {
                            "$set": {
                                "portfolioTrend": new_portfolio_trend,
                                "walletTrend": new_wallet_trend
                            }
                        }
                    )
                except Exception as e:
                    print(f"Error updating final trends for team {team_name}: {e}")
        except Exception as e:
            print(f"Error processing final team updates: {e}")
            flash(f"Error updating team data: {str(e)}", "error")
            return redirect("/dashboard")

        # Mark competition as completed
        try:
            mongo.db.competitions.update_one(
                {"_id": competition_obj_id},
                {
                    "$inc": {"currentRound": 1},
                    "$set": {"lastUpdated": datetime.now(timezone.utc), "completed": True}
                }
            )
            print(f"Competition {competition['competitionName']} marked as completed")
        except Exception as e:
            print(f"Error marking competition as completed: {e}")
            flash(f"Error completing competition: {str(e)}", "error")
            return redirect("/dashboard")

        flash("Competition completed successfully! Viewing final results.", "success")
        return redirect(f"/results/{competition_id}?completed=true")

    except Exception as e:
        print(f"Error completing competition: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Failed to complete competition: {str(e)}", "error")
        return redirect("/dashboard")

@app.route("/updateNext", methods=["POST"])
def next_round():
    if session.get('logged_in') != True:
        return redirect("/login")

    try:
        # Handle both form data and JSON
        competition_id = request.form.get("competition_id") or request.json.get("competition_id")
        if not competition_id:
            print("No competition_id provided in request")
            flash("Competition ID required", "error")
            return redirect("/dashboard")

        print(f"Updating to next round for competition: {competition_id}")

        try:
            competition_obj_id = ObjectId(competition_id)
            competition = mongo.db.competitions.find_one({"_id": competition_obj_id})
        except Exception as e:
            print(f"Error converting competition ID to ObjectId: {e}")
            flash(f"Invalid competition ID format: {str(e)}", "error")
            return redirect("/dashboard")

        if not competition:
            print(f"Competition not found with ID: {competition_id}")
            flash("Competition not found", "error")
            return redirect("/dashboard")

        print(f"Found competition: {competition.get('competitionName')}, current round: {competition.get('currentRound')}, total rounds: {competition.get('numberOfRounds')}")

        current_round = competition["currentRound"]
        number_of_rounds = competition["numberOfRounds"]

        if current_round >= number_of_rounds:
            print(f"Competition already completed. Current round: {current_round}, Number of rounds: {number_of_rounds}")
            flash("Competition already completed. Viewing results.", "info")
            return redirect(f"/results/{competition_id}")

        # Get current prices
        try:
            stocks = list(mongo.db.stocks.find({"competition_id": competition_obj_id}))
            print(f"Found {len(stocks)} stocks for this competition")

            current_prices = {}
            for stock in stocks:
                stock_id = stock["_id"]
                try:
                    round_price = mongo.db.rounds.find_one({
                        "competition_id": competition_obj_id,
                        "stock_id": stock_id,
                        "round_number": current_round
                    })
                    if round_price:
                        current_prices[stock["name"]] = round_price["price"]
                        print(f"Found price for stock {stock['name']}: {round_price['price']}")
                    else:
                        current_prices[stock["name"]] = stock["initial_price"]
                        print(f"Using initial price for stock {stock['name']}: {stock['initial_price']}")
                except Exception as e:
                    print(f"Error getting round price for stock {stock['name']}: {e}")
                    current_prices[stock["name"]] = stock["initial_price"]
        except Exception as e:
            print(f"Error fetching stocks: {e}")
            flash(f"Error fetching stocks: {str(e)}", "error")
            return redirect("/dashboard")

        # Update team trends
        try:
            teams = list(mongo.db.teams.find({"competition_id": competition_obj_id}))
            print(f"Found {len(teams)} teams for this competition")

            for team in teams:
                team_id = team["_id"]
                team_name = team.get("teamName", "Unknown")

                try:
                    holdings = decode_holdings(team.get("holding", ""))
                    wallet = team.get("wallet", 0)

                    portfolio_worth = sum(
                        quantity * current_prices.get(stock, 0)
                        for stock, quantity in holdings.items()
                    )

                    current_portfolio_trend = team.get("portfolioTrend", "")
                    current_wallet_trend = team.get("walletTrend", "")

                    new_portfolio_trend = f"{current_portfolio_trend},{portfolio_worth}" if current_portfolio_trend else f"{portfolio_worth}"
                    new_wallet_trend = f"{current_wallet_trend},{wallet}" if current_wallet_trend else f"{wallet}"

                    print(f"Updating team {team_name}: Portfolio worth: {portfolio_worth}, Wallet: {wallet}")

                    mongo.db.teams.update_one(
                        {"_id": team_id},
                        {
                            "$set": {
                                "portfolioTrend": new_portfolio_trend,
                                "walletTrend": new_wallet_trend
                            }
                        }
                    )
                except Exception as e:
                    print(f"Error updating trends for team {team_name}: {e}")
        except Exception as e:
            print(f"Error processing teams: {e}")
            flash(f"Error updating team data: {str(e)}", "error")
            return redirect("/dashboard")

        # Increment current round
        try:
            update_result = mongo.db.competitions.update_one(
                {"_id": competition_obj_id},
                {
                    "$inc": {"currentRound": 1},
                    "$set": {"lastUpdated": datetime.now(timezone.utc)}
                }
            )

            if update_result.modified_count != 1:
                print(f"Warning: Competition round update affected {update_result.modified_count} documents")
            else:
                print(f"Successfully incremented round for competition {competition['competitionName']}")
        except Exception as e:
            print(f"Error incrementing round: {e}")
            flash(f"Error incrementing round: {str(e)}", "error")
            return redirect("/dashboard")

        # Check if competition is now over (after incrementing the round)
        if current_round + 1 > number_of_rounds:
            print(f"Competition is now over. Completed all {number_of_rounds} rounds")
            # Remove the results validation check for this specific redirect
            flash("Competition Over! Viewing final results.", "success")
            return redirect(f"/results/{competition_id}?completed=true")

        print(f"Successfully advanced to round {current_round + 1} of {number_of_rounds}")
        # Direct redirect instead of JSON response
        if current_round + 1 == number_of_rounds:
            flash(f"Final round ({current_round + 1}) started! This is the last round.", "info")
        else:
            flash(f"Next round started successfully. Now on round {current_round + 1} of {number_of_rounds}.", "success")
        return redirect(f"/tradingPage/{competition_id}")
    except Exception as e:
        print(f"Error advancing round: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Failed to advance to next round: {str(e)}", "error")
        return redirect("/dashboard")

@app.route("/participant-logout")
def participant_logout():
    session.pop('participant_logged_in', None)
    session.pop('team_id', None)
    session.pop('team_name', None)
    return redirect("/participant-login")

if __name__ == "__main__":
    app.run(debug=True)
