"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from lib.models import *
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timeIssued = db.Column(db.DateTime, default = datetime.utcnow)

@app.route('/')
def home():
    return render_template('index.html')

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


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
