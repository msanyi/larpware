from flask import Flask
from database import db  # Import the 'db' object from the 'database' module
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import File, Digitalmarketlisting, App, AppType  # Import the necessary models
import sys
import random
from datetime import datetime, timedelta


def load_market_data(start_date):

    # Load JSON data from file
    with open('marketlistings.json', 'r') as f:
        listings_data = json.load(f)

    dateshift_delta = timedelta(days=0)
    if start_date is not None:
        print("start date is set to",start_date)
        first_datetime = datetime.fromisoformat(listings_data[0]["valid_from"])
        print("detected first datetime",first_datetime)
        raw_delta = start_date-first_datetime
        print("detected date shift:", raw_delta.days)
        dateshift_delta = timedelta(days=raw_delta.days+1)
        print("this will result in the first datetime becoming",first_datetime+dateshift_delta)

    # Iterate over the data and add each envelope to the database
    for listing_data in listings_data:
        print("importing listing",listing_data)
        listingType = listing_data["type"]
        marketType = listing_data["market_type"]
        price = listing_data["price"]
        valid_from = datetime.fromisoformat(listing_data["valid_from"])+dateshift_delta
        
        if listingType == "File":
            file_name = listing_data["file_name"]
            file_content = listing_data["file_content"]

            # Create the File entry
            new_file = File(name=file_name, content=file_content)

            db.session.add(new_file)
            db.session.commit()

            if marketType not in ['Public', 'Fixer', 'Darkweb']:
                raise ValueError("Invalid market type selected!")

            new_listing = Digitalmarketlisting(name=file_name,
                                            price=price,
                                            listing_type='File',
                                            description=f"File: {file_name}",
                                            market_type=marketType,
                                            file_id=new_file.id,
                                            valid_from=valid_from)

            db.session.add(new_listing)
            db.session.commit()

        elif listingType == "App":
            app_type_id = listing_data["app_type_id"]
            quantity = listing_data["quantity"]

            for _ in range(quantity):
                app_type = AppType.query.get(app_type_id)
                app_type_name = app_type.name
                app_name = f"{app_type_name}_{random.randint(1000, 9999)}"
                new_app = App(app_type_id=app_type_id, name=app_name)

                db.session.add(new_app)
                db.session.commit()

                # Create Digital Market Listing for the app

                # Check if market_type_selected is one of the allowed values.
                if marketType not in ['Public', 'Fixer', 'Darkweb']:
                    # Handle this error, maybe return a response or raise an exception
                    raise ValueError("Invalid market type selected!")

                item_desc = app_type.description
                new_listing = Digitalmarketlisting(name=app_type_name,
                                                    price=price,
                                                    listing_type='App',
                                                    description=item_desc,
                                                    market_type=marketType,
                                                    app_id=new_app.id,
                                                    valid_from=valid_from)

                db.session.add(new_listing)
                db.session.commit()


        elif listingType == "Physical Item":
            name = listing_data["name"]
            description = listing_data["description"]
            quantity = listing_data["quantity"]

            # Check if market_type_selected is one of the allowed values.
            if marketType not in ['Public', 'Fixer', 'Darkweb']:
                raise ValueError("Invalid market type selected!")

                # Create Digital Market Listing for the physical item.
            for _ in range(quantity):
                new_listing = Digitalmarketlisting(
                        name=name,
                        price=price,
                        listing_type='Physical Item',
                        description=description,
                        market_type=marketType,
                        valid_from=valid_from
                )
                db.session.add(new_listing)
                db.session.commit()
    


def main():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123qwe@localhost/cyberpunk_larpware?charset=utf8mb4'
    db_url = "localhost"
    db_user ="root"
    db_pass = "123qwe"
    start_date = None
    start_date = datetime.strptime('8/11/2023', "%d/%m/%Y")

    if len(sys.argv) == 4:
      db_url = sys.argv[1]
      db_user = sys.argv[2]
      db_pass = sys.argv[3]

    DATABASE_URI = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4'

    db.init_app(app)

    with app.app_context():
        load_market_data(start_date)
        db.session.commit()

if __name__ == "__main__":
    main()

print("Digital market listings imported successfully.")