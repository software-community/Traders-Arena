"""
Database models for the management portal
Author: Team SoftCom
"""
from flask_sqlalchemy.model import Model

class Competition(Model):
    """
    Class to refer to a particular competition being organized on the platform
    """
    pass

class Team(Model):
    """
    Class to refer to a particular team participating in a particular competition
    Contains information about what stocks are owned, how many, and wallet balance
    """
    pass

class Transaction(Model):
    """
    Class to refer to a particular transaction being made during a competition
    Contains information about buyer, seller, stock, price, quantity
    """
    pass

class Stock(Model):
    """
    Class to refer to a particular stock belonging to the fictional market of a certain competition
    Contains information about the stock's name, price, and quantity, and the closing price after every round
    """

class Round(Model):
    """
    Class to refer to a particular round of a competition
    Contains information about the round number, and news articles for that round
    """
    pass