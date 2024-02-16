from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from database import User, Inventory, App, AppType, File, Friendship, db
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from combat import log_app_usage
from navbar import NavBarInfo

inventory_app = Blueprint('inventory_app', __name__)


@inventory_app.route('/inventory', methods=['GET'])
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

    # Get the friend list for transfers
    friendships = Friendship.query.filter_by(user_id=session['user_id']).all()
    known_users = []
    for friendship in friendships:
        friend = User.query.filter_by(id=friendship.friend_id).first()
        if "Architecture Watchdog" not in friend.username:  # Check if the username doesn't contain the substring
            known_users.append({'id': friend.id, 'citynet': friend.citynet, 'username': friend.username})
    known_users = sorted(known_users, key=lambda d: d['username']) 

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

    return render_template('inventory.html', user=user, user_apps=user_apps, user_files=user_files, friends=known_users, headerinfo=NavBarInfo())


@inventory_app.route('/api/get-file-content/<int:file_id>', methods=['GET'])
def get_file_content(file_id):
    # (Existing authentication and verification code)

    file = File.query.get(file_id)

    if file:
        return jsonify(file.to_dict())
    else:
        return jsonify({'error': 'File not found'}), 404


@inventory_app.route('/api/scrub-file/<int:file_id>', methods=['POST'])
def scrub_file(file_id):
    print("scrub_file called")
    if not session.get('logged_in'):
        return jsonify(success=False, error="User not logged in")

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    print(f"user_id: {user_id}, file_id: {file_id}")
    if user is None:
        return jsonify(success=False, error="User does not exist")

    # Get the file
    file = File.query.get(file_id)
    print("file: ", file)
    if file is None or file.copied_by_id is None:
        return jsonify(success=False, error="File does not exist or does not have copied_by_id")

    # Check if user has a Scrub app
    scrub_app_inventory = db.session.query(Inventory).join(
        App, Inventory.app_id == App.id
    ).join(
        AppType, App.app_type_id == AppType.id
    ).filter(
        Inventory.user_id == user_id,
        AppType.name == 'Scrub',
        App.use_timestamp.is_(None)
    ).first()
    print("scrub_app_inventory: ", scrub_app_inventory)

    if scrub_app_inventory is None:
        return jsonify(success=False, error="No Scrub app available")

    # Log the usage of the Scrub app
    log_app_usage(scrub_app_inventory.app_id)

    # Perform the scrubbing operation
    file.copied_by_id = None
    db.session.delete(scrub_app_inventory)
    db.session.commit()

    return jsonify(success=True, file_content=file.to_dict())

@inventory_app.route('/api/user/files', methods=['GET'])
def get_user_files():
    print("get_user_files called")
    user = User.query.get(session.get('user_id'))
    if not user:
        return jsonify({'error': 'not logged in'}), 403

    files = [inventory.file for inventory in user.inventories if inventory.file is not None]
    print("files: ", files)
    return jsonify({'files': [file.to_dict() for file in files]})

@inventory_app.route('/api/user/apps', methods=['GET'])
def get_user_apps():
    print("get_user_apps called")
    user = User.query.get(session.get('user_id'))
    if not user:
        return jsonify({'error': 'not logged in'}), 403

    apps = [inventory.app for inventory in user.inventories if inventory.app is not None  and inventory.app.use_timestamp is None]
    print("files: ", apps)
    return jsonify({'apps': [app.to_dict() for app in apps]})

@inventory_app.route('/api/user/inventory', methods=['GET'])
def get_inventory_items():
    # Check if the user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('user_auth.user_login'))

    # Get the user_id from the session
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if user is None:
        # The user doesn't exist. Handle this situation as you see fit
        return redirect(url_for('user_auth.user_login'))

    apps = [inventory.app for inventory in user.inventories if inventory.app is not None  and inventory.app.use_timestamp is None]

    # From those inventories, we build a list of files
    user_files = [inventory.file for inventory in user.inventories if inventory.file is not None]

    inventory = []

    for app in apps:
        inventory.append({
            "id":app.id,
            "name":app.name,
            "type":"App"
        })

    for file in user_files:
        inventory.append({
            "id":file.id,
            "name":file.name,
            "type":"File"
        })

    return jsonify({"balance":user.balance, "inventory": inventory}), 200