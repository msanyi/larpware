# this is the beginning of endpointreg.py
from flask import Blueprint, request, jsonify, current_app  # Import the necessary modules from Flask
from werkzeug.security import generate_password_hash  # Import the function for password hashing
from database import User, db


register = Blueprint('register', __name__)  # Create a blueprint named 'register'


# class User(current_app.extensions['sqlalchemy'].db.Model):  # Define the User model class, which inherits from current_app.extensions['sqlalchemy'].db.Model
#     id = current_app.extensions['sqlalchemy'].db.Column(current_app.extensions['sqlalchemy'].db.Integer, primary_key=True)  # Define the 'id' column as an integer primary key
#     username = current_app.extensions['sqlalchemy'].db.Column(current_app.extensions['sqlalchemy'].db.String(80), unique=True, nullable=False)  # Define the 'username' column as a unique string with a maximum length of 80 characters, not nullable
#     password = current_app.extensions['sqlalchemy'].db.Column(current_app.extensions['sqlalchemy'].db.String(120), nullable=False)  # Define the 'password' column as a string with a maximum length of 120 characters, not nullable
#     balance = current_app.extensions['sqlalchemy'].db.Column(current_app.extensions['sqlalchemy'].db.Float, default=0)  # Define the 'balance' column as a float with a default value of 0


@register.route('/register', methods=['POST'])  # Decorator to specify the URL route and HTTP method for the following function
def register_user():
    username = request.json.get('username')  # Get the 'username' value from the JSON data of the request
    password = request.json.get('password')  # Get the 'password' value from the JSON data of the request
    if not username or not password:  # Check if username or password is missing
        return jsonify({'error': 'Username and password required'}), 400  # Return a JSON response with an error message and status code 400 (Bad Request)
    hashed_password = generate_password_hash(password)  # Generate a hashed password using the werkzeug.security.generate_password_hash() function
    new_user = User(username=username, password=hashed_password)  # Create a new User object with the username and hashed password
    current_app.extensions['sqlalchemy'].db.session.add(new_user)  # Add the new user to the database session
    current_app.extensions['sqlalchemy'].db.session.commit()  # Commit the changes to the database
    return jsonify({'message': 'User created successfully'}), 201  # Return a JSON response indicating successful user creation with status code 201 (Created)
# this is the end of endpointreg.py
