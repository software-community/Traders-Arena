"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from lib.models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

@app.route('/')
def home():
    return render_template('index.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
