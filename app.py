"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from lib.models import *
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Storing team details
team = []

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timeIssued = db.Column(db.DateTime, default = datetime.utcnow)


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


@app.route('/initialBuying', methods=["GET", "POST"])
def stocksIssue():
    if request.method == "POST":
        team = request.form['team']
        stock = request.form['stock']
        quantity = request.form['quantity']
        new_stock = Stock(team=team, stock=stock, quantity=quantity)
        db.session.add(new_stock)
        db.session.commit()
        return redirect(url_for('stocksIssue'))
    stocks = Stock.query.order_by(Stock.id.desc()).all()  # Order by id in descending order
    return render_template('initialBuying.html', stocks=stocks)

@app.route('/stock/<int:stock_id>')
def stock_detail(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    return render_template('stock_detail.html', stock=stock)

@app.route('/delete_stock/<int:stock_id>', methods=["POST"])
def delete_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    return redirect(url_for('stocksIssue'))



# Page for adding the teams (Shivang)
@app.route('/addTeam', methods=["GET", "POST"])
def addTeam():
    if request.method == "POST":
        newTeam = {
            "teamName": request.form["teamName"],
            "teamMembers": request.form["teamMembers"], 
        }
        if newTeam not in team:
            team.append(newTeam)
            print(team)
        return redirect(url_for('addTeam')) 
    return render_template("addTeam.html", teams=team)

# Removing the teams (Shivang)
@app.route('/removeTeam', methods=['POST'])
def removeTeam():
    teamName = request.form['teamName']
    global team
    team = [t for t in team if t['teamName'] != teamName]
    print(f"After removal: {team}")  
    return redirect(url_for('addTeam'))


@app.route('/stockNews')
def stockNews():
    return render_template('stockNews.html')

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
