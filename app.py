"""
Entrypoint for our management portal
Author: Team SoftCom
"""
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from lib.models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Storing team details
team = []

@app.route('/')
def home():
    return render_template('index.html')


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


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
