from sqlalchemy import create_engine
from flask import Flask
from database import db
import sys


def create_app():

    db_url = "localhost"
    db_user ="root"
    db_pass = "123qwe"
    if len(sys.argv) == 4:
      db_url = sys.argv[1]
      db_user = sys.argv[2]
      db_pass = sys.argv[3]

    alchemy_string = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}'
    root_uri = f'{alchemy_string}/?charset=utf8mb4'
    db_uri = f'{alchemy_string}/cyberpunk_larpware?charset=utf8mb4'
    engine = create_engine(root_uri)

    with engine.raw_connection().cursor() as cursor:
        cursor.execute('CREATE DATABASE IF NOT EXISTS cyberpunk_larpware CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    create_app()
