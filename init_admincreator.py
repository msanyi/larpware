# init_admincreator.py
from werkzeug.security import generate_password_hash
from getpass import getpass
from flask import Flask
from database import db, User
import sys

def create_app():
    app = Flask(__name__)
    db_url = "localhost"
    db_user ="root"
    db_pass = "123qwe"
    if len(sys.argv) == 4:
      db_url = sys.argv[1]
      db_user = sys.argv[2]
      db_pass = sys.argv[3]

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4'
    db.init_app(app)
    return app


def create_admin(app):
    with app.app_context():
        db.create_all()

        username = input("Enter the admin username: ")  # Prompt for admin username
        password = getpass("Enter the admin password: ")  # Prompt for admin password
        hashed_password = generate_password_hash(password)  # Hash the password

        new_admin = User(username=username, password=hashed_password, is_admin=True)  # Create new admin

        db.session.add(new_admin)  # Add new admin to the session
        db.session.commit()  # Commit the changes to the database

        print(f"Admin {username} created successfully.")  # Inform the user that the operation was successful


if __name__ == "__main__":
    admincreator_app = create_app()
    create_admin(admincreator_app)
# end of init_admincreator.py
