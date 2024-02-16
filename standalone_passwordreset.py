# standalone_passwordreset.py
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


def reset_password(app):
    with app.app_context():
        db.create_all()

        userid = input("Enter the user id to reset: ")  # Prompt for user id
        password = getpass("Enter the new password: ")  # Prompt for new password
        pass_hash = generate_password_hash(password)
        user = User.query.filter_by(id=userid).first()

        user.password = pass_hash
        user.passchanged = True
        db.session.commit()

        print(f"Password for {user.username} reset successfully to hash {pass_hash}.")  # Inform the user that the operation was successful


if __name__ == "__main__":
    passreset_app = create_app()
    reset_password(passreset_app)
# end of standalone_passwordreset.py