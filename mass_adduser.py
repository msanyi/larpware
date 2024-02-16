# begin of mass_adduser.py
import csv
import random
import os
import sys
import string
from flask import Flask
from database import db, User, UserOrganization, Organizations, AppType, App, Inventory  # Import the UserOrganization and Organizations
from werkzeug.security import generate_password_hash
from makefriends import make_friends_in_org


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
    with app.app_context():
        db.create_all()  # Create any missing database tables/columns
    return app


def generate_password():
    # Choose from these characters: a-z, A-Z, 0-9
    characters = string.ascii_letters + string.digits
    # Generate a random 4 character password
    password = ''.join(random.choice(characters) for _ in range(4))
    return password


def user_exists(username):
    return db.session.query(User.query.filter(User.username == username).exists()).scalar()


def create_user(username, is_netrunner, is_fixer, balance, password, org_id, app_list):
    user = User(
        username=username,
        password=generate_password_hash(password),
        is_netrunner=is_netrunner,
        is_fixer=is_fixer,
        balance=int(balance),
        citynet=generate_citynet()
    )
    db.session.add(user)
    db.session.flush()  # Flush to get the id of the user

    if org_id is not None:  # If an organization id was provided
        organization = db.session.get(Organizations, org_id)
        if organization is not None:  # If the organization exists
            user_org = UserOrganization(
                user_organization_id=user.id,
                organization_id=org_id
            )
            db.session.add(user_org)

    # Parse and add apps

    for app_data in app_list:
        if len(app_data) == 0:
            continue
        app_type_id, app_quantity = map(int, app_data.split(":"))
        app_type = db.session.get(AppType, app_type_id)
        print("adding app",app_type_id,app_type)
        if app_type is not None:  # If the app type exists
            for _ in range(app_quantity):
                new_app = App(
                    app_type_id=app_type.id,
                    name=f"{app_type.name}_{random.randint(1000, 9999)}",  # Change this to how you want to generate app names
                    use_timestamp=None
                )
                db.session.add(new_app)
                db.session.flush()  # Flush to get the id of the app

                # Add app to the inventory
                inventory = Inventory(user_id=user.id, app_id=new_app.id)
                db.session.add(inventory)

    db.session.commit()


def clear_user_inventory(user_id):
    """Clears the user's inventory"""
    Inventory.query.filter_by(user_id=user_id).delete()
    db.session.commit()


def add_apps_to_inventory(user_id, app_list):
    """Adds apps to the user's inventory"""

    for app_data in app_list:
        if len(app_data) == 0:
            continue
        app_type_id, app_quantity = map(int, app_data.split(":"))
        app_type = db.session.get(AppType, app_type_id)
        if app_type is not None:  # If the app type exists
            for _ in range(app_quantity):
                new_app = App(
                    app_type_id=app_type.id,
                    name=f"{app_type.name}_{random.randint(1000, 9999)}",  # Generate app names
                    use_timestamp=None
                )
                db.session.add(new_app)
                db.session.flush()  # Flush to get the id of the app

                # Add app to the inventory
                inventory = Inventory(user_id=user_id, app_id=new_app.id)
                db.session.add(inventory)
                print("added app", new_app.name)

    db.session.commit()


def update_user(username, balance, app_list):
    """Updates the user's balance and clears their inventory"""
    user = User.query.filter_by(username=username).first()
    user.balance = int(balance)
    db.session.commit()
    clear_user_inventory(user.id)
    add_apps_to_inventory(user.id, app_list)


def main():
    app = create_app()
    filename = os.path.join('users', 'userlist.txt')

    with app.app_context():
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    username, is_fixer, is_netrunner, balance, org_id, *app_data = row
                    is_netrunner = True if is_netrunner.lower() == 'y' else False
                    is_fixer = True if is_fixer.lower() == 'y' else False
                    org_id = int(org_id) if org_id else None

                    # Concatenate app_data elements and then split on semicolon
                    print("app data raw is",app_data);
                    app_data_str = ",".join(app_data)
                    print("processed string is",app_data_str)
                    app_list = app_data_str.split(";")
                    print("processed app list is",app_list)

                    if user_exists(username):
                        update_user(username, balance, app_list)
                        print(f"updated user {username}")
                    else:
                        password = generate_password()
                        create_user(username, is_netrunner, is_fixer, balance, password, org_id, app_list)
                        print(f"created user {username}")
                        citynet_number = User.query.filter_by(username=username).first().citynet
                        with open('users_with_default_passwords.txt', 'a', encoding='utf-8') as pw_file:
                            pw_file.write(f'{username},{password},{citynet_number}\n')
                except Exception as e:
                    print(f"Error processing the line: {row}")
                    raise e
        # uncomment this when initializing the entire database from scratch
        print("make friends is being SKIPPED, do not be surprised about this")
        # make_friends_in_org()
        db.session.commit()
        print("db session committed, exiting")


def generate_citynet():
    while True:
        citynet = random.randint(1000000, 9999999)
        user = User.query.filter_by(citynet=citynet).first()
        if not user:
            return citynet


if __name__ == "__main__":
    main()

# end of mass_adduser.py
