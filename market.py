from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, session, request
from database import db, Digitalmarketlisting, Organizations, Organizationavailability, App, AppType, User, Inventory, File, Couriertask
from sqlalchemy.orm import aliased
from sqlalchemy import func
from sqlalchemy import or_
from serializer_helpers import user_to_dict, app_type_to_dict, file_to_dict, digitalmarketlisting_to_dict
from navbar import NavBarInfo
from datetime import datetime


client_market_app = Blueprint('client_market_app', __name__)


@client_market_app.route('/market', methods=['GET'])
def show_market():
    # Check if the user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('user_auth.user_login'))

    # Get the user_id from the session
    user_id = session.get('user_id')

    # Fetch the user from the database
    user = User.query.get(user_id)

    if user is None:
        # The user doesn't exist. Handle this situation as you see fit
        return redirect(url_for('user_auth.user_login'))

    # Fetch all the listings available for the user
    available_items = get_listings_for_user(user)
    # Flatten the dictionary to a single list of Digitalmarketlisting objects
    all_listings = [item for sublist in available_items.values() for item in sublist]

    # Convert session to dictionary
    session_dict = dict(session)
    # Count each AppType in the user's inventory
    inventory_counts = Inventory.query.join(
        App, Inventory.app_id == App.id
    ).filter(
        Inventory.user_id == user_id
    ).filter(
        App.use_timestamp.is_(None)
    ).with_entities(
        App.app_type_id, func.count(App.app_type_id)
    ).group_by(
        App.app_type_id
    ).all()

    # Fetch details of each AppType
    app_types = AppType.query.filter(AppType.id.in_([item[0] for item in inventory_counts])).all()
    app_types_dict = {app_type.id: app_type for app_type in app_types}

    # Prepare data for the template
    user_apps = [{'app_type': app_types_dict[item[0]], 'count': item[1]} for item in inventory_counts]

    # Get the inventories for the current user for files
    user_files_inventories = Inventory.query.filter_by(user_id=user_id).filter_by(app_id=None).all()

    # From those inventories, we build a list of files
    user_files = [inventory.file for inventory in user_files_inventories]

    # Assuming you want to sort user_files based on id
    user_files.sort(key=lambda file: file.id)

    # Serialize the user object
    serialized_user = user_to_dict(user)

    # Serialize the items
    serialized_items = [digitalmarketlisting_to_dict(item) for item in all_listings]

    # Serialize user_apps' app_type
    for app in user_apps:
        app['app_type'] = app_type_to_dict(app['app_type'])

    # Serialize user_files
    serialized_user_files = [file_to_dict(file) for file in user_files]

    # return render_template('market.html', user=user, items=available_items, user_apps=user_apps, user_files=user_files, session_data=session)
    return render_template('market.html', user=serialized_user, items=serialized_items, user_apps=user_apps, user_files=serialized_user_files, session_data=session_dict, headerinfo=NavBarInfo())


def get_listings_for_user(user):
    listings = {
        "own_organization": [],
        "other_organizations": {},
        "public": [],
        "dark_web": [],
        "fixer": []
    }

    # Fetch all listing IDs present in Couriertask
    courier_listings_ids = [task.listing_id for task in Couriertask.query.all()]

    # 1. Own Organization Listing
    own_orgs = [org.organization_id for org in user.organizations if not org.endtime]
    for org_id in own_orgs:
        org_specific_listings = Digitalmarketlisting.query.join(
            Organizationavailability
        ).filter(
            Organizationavailability.organization_id == org_id,
            Digitalmarketlisting.market_type == "Organization Specific",
            Digitalmarketlisting.id.notin_(courier_listings_ids),
            or_(
                Digitalmarketlisting.valid_from == None,
                Digitalmarketlisting.valid_from < datetime.utcnow()
            )
        ).all()
        listings["own_organization"].extend(org_specific_listings)

    # 2. Other Organization Listings
    other_orgs = [org.organization_id for org in user.organizations if org.endtime]
    for org_id in other_orgs:
        org_specific_listings = Digitalmarketlisting.query.join(
            Organizationavailability
        ).filter(
            Organizationavailability.organization_id == org_id,
            Digitalmarketlisting.market_type == "Organization Specific",
            Digitalmarketlisting.id.notin_(courier_listings_ids),
            or_(
                Digitalmarketlisting.valid_from == None,
                Digitalmarketlisting.valid_from < datetime.utcnow()
            )
        ).all()
        listings["other_organizations"][org_id] = org_specific_listings

    # Listings filtering based on organization availability
    all_orgs = own_orgs + other_orgs
    non_org_specific_listings = Digitalmarketlisting.query.outerjoin(
        Organizationavailability
    ).filter(
        Organizationavailability.id.is_(None),  # Listings without any specific organization
        Digitalmarketlisting.id.notin_(courier_listings_ids)
    ).all()

    # 3. Public Listing
    public_listings = Digitalmarketlisting.query.join(
        Organizationavailability, isouter=True
    ).filter(
        or_(
            Organizationavailability.organization_id.in_(all_orgs),
            Digitalmarketlisting.id.in_([listing.id for listing in non_org_specific_listings])
        ),
        Digitalmarketlisting.market_type == "Public",
            or_(
                Digitalmarketlisting.valid_from == None,
                Digitalmarketlisting.valid_from < datetime.utcnow()
            )
    ).all()
    listings["public"].extend(public_listings)

    # 4. Netrunner Specific (Dark Web) Listing
    if user.is_netrunner:
        dark_web_listings = Digitalmarketlisting.query.join(
            Organizationavailability, isouter=True
        ).filter(
            or_(
                Organizationavailability.organization_id.in_(all_orgs),
                Digitalmarketlisting.id.in_([listing.id for listing in non_org_specific_listings])
            ),
            Digitalmarketlisting.market_type == "Darkweb",
            or_(
                Digitalmarketlisting.valid_from == None,
                Digitalmarketlisting.valid_from < datetime.utcnow()
            )
        ).all()
        listings["dark_web"].extend(dark_web_listings)

    # 5. Fixer Listings
    if user.is_fixer:
        fixer_listings = Digitalmarketlisting.query.join(
            Organizationavailability, isouter=True
        ).filter(
            or_(
                Organizationavailability.organization_id.in_(all_orgs),
                Digitalmarketlisting.id.in_([listing.id for listing in non_org_specific_listings])
            ),
            Digitalmarketlisting.market_type == "Fixer",
            or_(
                Digitalmarketlisting.valid_from == None,
                Digitalmarketlisting.valid_from < datetime.utcnow()
            )
        ).all()
        listings["fixer"].extend(fixer_listings)

    print("***************** listings: ", listings)
    return listings


def purchase_item(user, item_id):
    # Check user balance and item price
    item = Digitalmarketlisting.query.get(item_id)
    print(f"User balance: {user.balance}, Item price: {item.price}")

    if user.balance < item.price:
        print("Purchase halted due to insufficient balance.")
        return "ERROR: Insufficient balance!"

    user.balance -= item.price
    print(f"User balance after deduction: {user.balance}")

    if item.listing_type == "App":
        print("Item type is App")
        # Add to digital inventory
        existing_entry = Inventory.query.filter_by(user_id=user.id, app_id=item.app_id).first()
        if existing_entry:
            print("Existing entry for App. What to do?")
        else:
            print("New entry for App. Adding to inventory.")
            new_entry = Inventory(user_id=user.id, app_id=item.app_id)
            db.session.add(new_entry)

    elif item.listing_type == "File":
        print("Item type is File")
        # Add to digital inventory
        existing_entry = Inventory.query.filter_by(user_id=user.id, file_id=item.file_id).first()
        if not existing_entry:
            print("New entry for File. Adding to inventory.")
            new_entry = Inventory(user_id=user.id, file_id=item.file_id)
            db.session.add(new_entry)
        else:
            print("Existing entry for File. What to do?")

    else:
        print(f"Unhandled item listing type: {item.listing_type}")

    db.session.commit()
    print("Database committed.")

    delete_item_from_market(item_id)
    return f"Purchase successful!"


def delete_item_from_market(item_id):
    item = Digitalmarketlisting.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        print(f"Item with ID {item_id} removed from Digitalmarketlisting")
        return True
    else:
        print(f"Failed to find item with ID {item_id} in Digitalmarketlisting")
        return False


def buy_file(user, file_id):
    # Fetch the file
    file = File.query.get(file_id)

    # Fetch the associated digital market listing for the file
    listing = Digitalmarketlisting.query.filter_by(file_id=file_id).first()

    # Check if listing exists and if the user has enough balance
    if not listing or user.balance < listing.price:
        return "ERROR: Insufficient balance!"

    # Deduct the price from the user's balance
    user.balance -= listing.price

    # Mark the user as the original owner of the file
    file.original_owner_id = user.id

    # Add the file to the user's inventory
    new_entry = Inventory(user_id=user.id, file_id=file.id)  # Using file.id, but this is the same as file_id in this context.
    db.session.add(new_entry)

    # Delete the item from the market
    if not delete_item_from_market(listing.id):
        db.session.rollback()
        return "Error while deleting the item from the market after purchase."

    db.session.commit()
    return "Purchase successful"


def buy_hardware(user, item_id):
    # 1. Check user balance and item price
    item = Digitalmarketlisting.query.get(item_id)
    print(f"User balance: {user.balance}, Item price: {item.price}")

    if user.balance < item.price:
        print("Hardware purchase halted due to insufficient balance.")
        return "ERROR: Insufficient balance!"

    # 2. Deduct the item's price from user's balance
    user.balance -= item.price
    print(f"User balance after deduction: {user.balance}")

    # 3. Add a new record to Couriertask
    new_task = Couriertask(listing_id=item_id, buyer_id=user.id, status='New')
    db.session.add(new_task)

    # 4. Commit changes to the database
    db.session.commit()
    print("Database committed for hardware purchase.")

    return "Purchase successful, a courier will see you soon"


def show_inventory():
    # Check if the user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('user_auth.user_login'))

    # Get the user_id from the session
    user_id = session.get('user_id')

    # Fetch the user from the database
    user = User.query.get(user_id)

    if user is None:
        # The user doesn't exist. Handle this situation as you see fit
        return redirect(url_for('user_auth.user_login'))

    # Count each AppType in the user's inventory
    inventory_counts = Inventory.query.join(
        App, Inventory.app_id == App.id
    ).filter(
        Inventory.user_id == user_id
    ).filter(
        App.use_timestamp.is_(None)  # This is the new line to filter by NULL use_timestamp
    ).with_entities(
        App.app_type_id, func.count(App.app_type_id)
    ).group_by(
        App.app_type_id
    ).all()

    # Fetch details of each AppType
    app_types = AppType.query.filter(AppType.id.in_([item[0] for item in inventory_counts])).all()
    app_types_dict = {app_type.id: app_type for app_type in app_types}  # create a dictionary for quick lookup

    # Prepare data for the template
    user_apps = [{'app_type': app_types_dict[item[0]], 'count': item[1]} for item in inventory_counts]

    # Get the inventories for the current user for files
    user_files_inventories = Inventory.query.filter_by(user_id=user_id).filter_by(app_id=None).all()

    # From those inventories, we build a list of files
    user_files = [inventory.file for inventory in user_files_inventories]

    # Assuming you want to sort user_files based on id
    user_files.sort(key=lambda file: file.id)

    return render_template('inventory.html', user=user, user_apps=user_apps, user_files=user_files, headerinfo=NavBarInfo())


def has_sufficient_balance(user_id, item_price):
    user = User.query.get(user_id)
    return user.balance >= item_price


@client_market_app.route('/api/has_sufficient_balance/<int:user_id>/<float:price>', methods=['GET'])
def api_has_sufficient_balance(user_id, price):
    has_balance = has_sufficient_balance(user_id, price)
    return jsonify({"hasSufficientBalance": has_balance})


@client_market_app.route('/api/purchase', methods=['POST'])
def api_purchase_item():
    user_id = session.get('user_id')  # Adjust this to however you're getting the current user's ID
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('user_auth.user_login'))
    items = request.json.get('items')

    item = None
    for item_id in items:
        item = Digitalmarketlisting.query.get(item_id)
        if item is not None:
            break
    
    if not item:
        message = "ERROR: The item you were looking for was already bought by someone."
    else:
        # Determine what type of item and execute the appropriate purchase function
        if item.listing_type == "App":
            message = purchase_item(user, item_id)
        elif item.listing_type == "File":
            message = buy_file(user, item.file_id)
        elif item.listing_type == "Physical Item":
            message = buy_hardware(user, item_id)
        else:
            message = "ERROR: Unknown item type"

    flash(message)
    return url_for('user_app.client_market_app.show_market')