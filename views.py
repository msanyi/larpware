# views.py
from flask import Blueprint
# from auth import auth  # Import the 'auth' blueprint module
from transactions import transactions  # Import the 'transactions' blueprint module
from admin import admin  # Import the 'admin' blueprint
# from user_app import app as user_app  # later if I can separate parts of user_app.py to blueprints
# from friends_app import friends_app  # yet to be created
from messaging_app import messaging_app  # Import the 'messaging_app' blueprint module
from endpointreg import register

# Create a list of all blueprints
# blueprints = [auth, transactions, admin, user_app, friends_app]  # ...and so on, adding future blueprints here
blueprints = [auth, transactions, admin, register, messaging_app]
