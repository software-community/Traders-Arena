"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from flask import Flask, render_template, request, redirect
app = Flask(__name__)

# Competitions are stored as object of this class
class CompetitionObj:
    def __init__(self,competitionName,numberOfRounds,walletSize):
        self.competitionName=competitionName
        self.numberOfRounds=numberOfRounds
        self.walletSize=walletSize
        self.stocks={}
        self.rounds={}

# Competition - contains all the added compeititions as (key: Competition Name, value: corresponding object)       
Competition={}


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# Stock_Admin - portal to add a Competition and involved elements (stocks, wallet size etc)
@app.route('/stock_admin', methods=['GET', 'POST'])
def stock_admin():
    if request.method == 'POST':
        competitionName = request.form.get('competitionName')
        numberOfRounds = int(request.form.get('rounds'))
        walletSize =request.form.get('walletSize')
        obj=CompetitionObj(competitionName, numberOfRounds, walletSize)

        stockNames = request.form.getlist('stockName')
        priceList= request.form.getlist('price')

        for i in range(len(stockNames)):
            obj.stocks[stockNames[i]]=priceList[i]
            obj.rounds[stockNames[i]]=request.form.getlist(f'round-{stockNames[i]}')

        Competition[competitionName]=obj
        return redirect('/stock_admin')
    return render_template('stock_admin.html', competition=Competition)

# Dashboard to view all added Competitions (and the involved elements - Stocks, Prices etc)
@app.route('/dashboard', methods=["GET","POST"])
def receive_data():
    return render_template('dashboard.html', competition=Competition)

# Delete Competition from Dashboard
@app.route('/delete-competition', methods=['POST'])
def delete_competition():
    key_to_delete = request.form.get('keyToDelete')
    if key_to_delete in Competition:
        del Competition[key_to_delete]
    return redirect('/dashboard')


if __name__ == '__main__':
    app.run(debug=True)
