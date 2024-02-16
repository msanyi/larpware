# scanner.py

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from database import Qrcode, Network, Node, NodeType, NodeUsers, db, Inventory, App, File, User, AppType
from datetime import datetime, timedelta
from navbar import NavBarInfo
from combat import log_app_usage
from sqlalchemy import func


scanner_app = Blueprint('scanner_app', __name__)


def add_user_to_node(user_id, node_id):
    """Add a user to a node."""
    node_user = NodeUsers(user_id=user_id, node_id=node_id)
    db.session.add(node_user)
    db.session.commit()


@scanner_app.route('/scanner', methods=['GET', 'POST'])
def scanner_route():
    print("scanner_route called")
    if request.method == 'POST':
        data = request.get_json()
        qrcode = data.get('qrcode', None) if data else None
        print("data: ", data)
        print("qrcode: ", qrcode)

        if not qrcode:
            return jsonify({"message": "No qrcode data received."}), 400

        qrcode_in_db = Qrcode.query.filter_by(id=qrcode).first()
        print("qrcode_in_db: ", qrcode_in_db)

        if qrcode_in_db is None:
            return jsonify({"message": "Invalid qrcode."}), 400

        if qrcode_in_db.qrcodetype == 'accesspoint':
            print("accesspoint route")
            # Fetch the network associated with this QR code
            network = Network.query.filter_by(organization_id=qrcode_in_db.organization_id).first()
            print("network in scanner: ", network)

            if network is None:
                return jsonify({"message": "Invalid network."}), 400

            # Fetch the nodes in the network
            nodes = Node.query.filter_by(network_id=network.id).order_by(Node.order).all()

            if not nodes:
                return jsonify({"message": "No nodes in this network."}), 400

            # Fetch the entry node
            entry_node = nodes[0]

            # Fetch the node type of the entry node
            entry_node_type = NodeType.query.get(entry_node.node_type_id)

            if entry_node_type is None:
                return jsonify({"message": "Invalid node type."}), 400

            # Check if user is a netrunner
            is_netrunner = session.get('is_netrunner', False)

            # If user is a netrunner, redirect them to the network page
            if is_netrunner:
                print("is_netrunner route")
                session['current_qrcode'] = qrcode  # Store the qrcode in the session
                return jsonify(
                    {"redirect_url": url_for('user_app.scanner_app.access_network', network_id=network.id, _external=True),
                     "network_name": network.name, "is_netrunner": True}), 200
            # If user is not a netrunner, just inform them about the network
            else:
                return jsonify({"message": f"You found a network with the name: {qrcode}", "network_name": qrcode, "is_netrunner": False}), 200

        if qrcode_in_db.qrcodetype in ['inventoryadd_app', 'inventoryadd_file']:
            print("inventoryadd_app, inventoryadd_file route")
            user_id = session.get('user_id')
            if not user_id:
                print("User not authenticated")
                return jsonify({"message": "User not authenticated."}), 400

            target_id = qrcode_in_db.targetid
            print("target_id: ", target_id)
            if not target_id:
                print("Invalid QR code. No target ID")
                return jsonify(message= "Data Shard is empty.", qrcodetype="inventory"), 400

            # Fetch app or file based on qrcodetype
            item_type = App if qrcode_in_db.qrcodetype == 'inventoryadd_app' else File
            item = item_type.query.get(target_id)
            print("item: ", item.name)
            if not item:
                return jsonify(message= "Data Shard is empty.", qrcodetype="inventory"), 400

            # Return success message
            return jsonify(message=f"Data Shard contains: {item.name}.", qrcodetype="inventory", qrcode=qrcode), 200

        if qrcode_in_db.qrcodetype == 'inventoryadd_cash':
            print("inventoryadd_cash route")
            print("qrcode_in_db: ", qrcode_in_db)

            user_id = session.get('user_id')
            print("user_id: ", user_id)

            if not user_id:
                print("no user_id")
                return jsonify({"message": "User not authenticated."}), 400
            
            cash = qrcode_in_db.targetid
            if not cash:
                return jsonify(message= "Data Shard is empty.", qrcodetype="inventory"), 400
            
            return jsonify(message=f"Data Shard contains a cryptokey worth {cash} €$", qrcodetype="inventory", qrcode=qrcode), 200


        if qrcode_in_db.qrcodetype == 'lock':
            print("lock route")
            print("qrcode_in_db: ", qrcode_in_db)

            user_id = session.get('user_id')
            print("user_id: ", user_id)

            if not user_id:
                print("no user_id")
                return jsonify({"message": "User not authenticated."}), 400

            user = User.query.get(user_id)
            if not user:
                return jsonify({"message": "User not found."}), 400

            # Fetch user's organization IDs
            user_org_ids = [org_rel.organization_id for org_rel in user.organizations if org_rel.endtime is None or org_rel.endtime > datetime.utcnow()]
            print("user's organization ids: ", user_org_ids)

            lock_organization_id = qrcode_in_db.organization_id
            print("lock_organization_id: ", lock_organization_id)

            user_is_in_organization = lock_organization_id in user_org_ids
            print("user_is_in_organization: ", user_is_in_organization)

            # Query for Lockpick AppType
            lockpick_app_type = AppType.query.filter_by(name='Lockpick').first()
            if not lockpick_app_type:
                print("no lockpick app type, exiting function")
                return jsonify({"message": "Lockpick app type not found."}), 400

            # Check the user's inventory for unused Lockpick apps
            lockpick_apps = Inventory.query.join(App, App.id == Inventory.app_id).filter(
                Inventory.user_id == user_id,
                App.app_type_id == lockpick_app_type.id,
                App.use_timestamp.is_(None)
            ).all()
            lockpick_count = len(lockpick_apps)
            print("Number of unused Lockpick apps in inventory: ", lockpick_count)
            # Check if Lockpick is still active
            lockpick_expiry = session.get('lockpick_expiry')
            print("lockpick_expiry: ", lockpick_expiry)
            if lockpick_expiry and datetime.utcnow().timestamp() > lockpick_expiry:
                session['lockpick_active'] = False

            if user_is_in_organization or session.get('lockpick_active'):
                print("ACCESS GRANTED")
                return jsonify(success=True, message="ACCESS GRANTED", action="grantAccess", qrcodetype="lock"), 200

            else:
                if len(lockpick_apps) == 0:
                    print("ACCESS DENIED, no lockpicks")
                    return jsonify(success=False, message="Electronic lock - ACCESS DENIED.", action="noLockpicks", qrcodetype="lock"), 200

                else:
                    print("Lockpick apps in inventory, let's notify user that lockpick can be used")
                    return jsonify(success=False, message="Electronic lock - ACCESS DENIED.", action="denyAccess", lockpickCount=lockpick_count, qrcodetype="lock"), 200

        return jsonify({"message": f"Received qrcode: {qrcode}"}), 200

    # If the request is not a POST (i.e., it's a GET), check if user is an admin and pass the access point qrcodes to the template
    is_admin = session.get('is_admin', False)
    print("is_admin: ", is_admin)

    qrcodes = []
    if is_admin:
        # print("user is admin, let's pass teh qr codes")
        qrcodes = Qrcode.query.filter_by(qrcodetype='accesspoint').all()
        # print("qrcodes: ", qrcodes)

    return render_template('scanner.html', qrcodes=qrcodes, headerinfo=NavBarInfo())

@scanner_app.route('/add_to_inventory', methods=['POST'])
def add_to_inventory():
    print("add_to_inventory called")
    data = request.get_json()
    qrcode = data.get('qrcode', None) if data else None
    print("data: ", data)
    print("qrcode: ", qrcode)

    if not qrcode:
        return jsonify({"message": "No qrcode data received."}), 400

    qrcode_in_db = Qrcode.query.filter_by(id=qrcode).first()
    print("qrcode_in_db: ", qrcode_in_db)

    if qrcode_in_db is None or qrcode_in_db.qrcodetype in ["accesspoint","lock"]:
        return jsonify({"message": "Invalid qrcode."}), 400

    
    if qrcode_in_db.qrcodetype in ['inventoryadd_app', 'inventoryadd_file', 'inventoryadd_cash']:
        print("inventoryadd_app, inventoryadd_file, inventoryadd_cash route")
        user_id = session.get('user_id')
        if not user_id:
            print("User not authenticated")
            return jsonify({"message": "User not authenticated."}), 400

        user = User.query.get(user_id)
        print("user: ", user)
        if not user:
            print("User not found")
            return jsonify({"message": "User not found."}), 400

        target_id = qrcode_in_db.targetid
        print("target_id: ", target_id)
        if not target_id:
            print("Invalid QR code. No target ID")
            return jsonify({"message": "Invalid QR code. No target ID."}), 400

        if qrcode_in_db.qrcodetype in ['inventoryadd_app', 'inventoryadd_file']:
            # Fetch app or file based on qrcodetype
            item_type = App if qrcode_in_db.qrcodetype == 'inventoryadd_app' else File
            item = item_type.query.get(target_id)
            print("item: ", item)
            if not item:
                return jsonify({"message": "Item not found."}), 400

            # Add to inventory
            inventory_item = Inventory(user_id=user_id, app_id=item.id if isinstance(item, App) else None,
                                           file_id=item.id if isinstance(item, File) else None)
            print("inventory_item: ", inventory_item)
            db.session.add(inventory_item)
            # Clear the Qrcode record
            qrcode_in_db.targetid = None
            db.session.commit()

            # Return success message
            return jsonify({"message": f"{item.name} added to inventory!"}), 200
        else:
            cash = qrcode_in_db.targetid
            user.balance += cash
            # Clear the Qrcode record
            qrcode_in_db.targetid = None
            db.session.commit()

            # Return success message
            return jsonify({"message": f"Cryptokey unlocked, {cash} €$ added to your Balance!"}), 200
        
        

        
    return jsonify({"message": f"Received qrcode: {qrcode}"}), 200

@scanner_app.route('/use_lockpick', methods=['POST'])
def use_lockpick():
    print("use_lockpick called")
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"message": "User not authenticated."}), 400

    lockpick_app_type = AppType.query.filter_by(name='Lockpick').first()

    # Fetch Lockpick app instances
    lockpick_app_instances = Inventory.query.join(App, App.id == Inventory.app_id).filter(
        Inventory.user_id == user_id,
        App.app_type_id == lockpick_app_type.id,
        App.use_timestamp.is_(None)
    ).all()

    lockpickappid = lockpick_app_instances[0].app_id if lockpick_app_instances else None
    print("lockpick_app_instance: ", lockpick_app_instances)

    if not lockpickappid:
        print("no lockpickappid")
        return jsonify({"message": "Lockpick app not found."}), 400

    # Fetch one active Lockpick app from the user's inventory
    lockpick_app = Inventory.query.filter_by(user_id=user_id, app_id=lockpickappid).first()
    print("lockpick_app: ", lockpick_app)

    if lockpick_app:
        log_app_usage(lockpick_app.app_id)  # Deactivate the Lockpick app
        session['lockpick_active'] = True  # Set the session variable to grant access
        session['lockpick_expiry'] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()  # Set the expiry time
        print("session lockpick_active: ", session['lockpick_active'])
        print("session lockpick_expiry: ", session['lockpick_expiry'])
        return jsonify({"message": "Lockpick activated", "counter": 5 * 60}), 200
    else:
        return jsonify({"message": "No active Lockpick app available."}), 400


@scanner_app.route('/access_network/<int:network_id>', methods=['GET', 'POST'])
def access_network(network_id):
    print("scanner_app access_network route called")
    # If the user is a netrunner, then redirect them to the network_page
    if session.get('is_netrunner', False):
        entry_node = Node.query.filter_by(network_id=network_id, order=0).first()
        if entry_node is None:
            # Remove the user from all other nodes
            # remove_user_from_all_nodes(session['user_id'])
            return jsonify({"message": "No entry node for this network."}), 400
        # Add the user to the entry node
        add_user_to_node(session['user_id'], entry_node.id)
        print("scanner_app access_network route add_user_to_node path called, redirecting to netrunning")

        if "black_ic_session" in session:
            del session["black_ic_session"]
            print("black_ic_session is deleted.")

        return redirect(url_for('user_app.netrunning.netrunning'))

    # Otherwise, return a message to the user.
    else:
        network = Network.query.get(network_id)
        if network is None:
            print("scanner_app access_network route Invalid network called")
            return jsonify({"message": "Invalid network."}), 400
        print("scanner_app access_network route Network access successful redirect called")

        session_data = session.get("black_ic_session")
        print("session_data in Scanner:: ", session_data)
        del session["black_ic_session"]  # Making sure no previously used BIC session
        session_data = session.get("black_ic_session")
        print("session_data after session delete in Scanner:: ", session_data)
        return jsonify({"message": "Network access successful.", "network_name": network.name, "redirect_url": url_for('user_app.netrunning.network_page', network_id=network_id)}), 200



@scanner_app.route('/put_to_shard', methods=['POST'])
def put_to_shard():
    print("put_to_shard called")
    data = request.get_json()
    qrcode = data.get('qrcode', None)
    item_type = data.get('item_type', None)
    item_id = data.get('item_id', None)
    print("data: ", data)
    print("qrcode: ", qrcode)
    print("item_type: ", item_type)
    print("item_id: ", item_id)

    user_id = session.get('user_id')

    if not qrcode:
        return jsonify({"message": "No qrcode data received."}), 400

    qrcode_in_db = Qrcode.query.filter_by(id=qrcode).first()
    print("qrcode_in_db: ", qrcode_in_db)

    if qrcode_in_db is None or qrcode_in_db.qrcodetype in ["accesspoint","lock"]:
        return jsonify({"message": "Invalid qrcode."}), 400
    
    if qrcode_in_db.targetid is not None:
        return jsonify({"message":"Shard is not empty."}), 400

    if qrcode_in_db.qrcodetype in ['inventoryadd_file', 'inventoryadd_app', 'inventoryadd_cash']:
    # If Qrcode is found, update the targetid
        if item_type in ['File']:
            print("inventoryadd_file")
            sender_inventory = Inventory.query.filter_by(user_id=user_id, file_id=item_id).first()
            if not sender_inventory:
                return jsonify({'error': 'You do not have the file in your inventory'}), 404
            # Remove the file from the sender's inventory
            db.session.delete(sender_inventory)
            db.session.commit()
            qrcode_in_db.qrcodetype = 'inventoryadd_file'
        elif item_type in ['App']:
            print("inventoryadd_app path")
            sender_inventory = Inventory.query.filter_by(user_id=user_id, app_id=item_id).first()
            if not sender_inventory:
                return jsonify({'error': 'You do not have the app in your inventory'}), 404
            # Remove the file from the sender's inventory
            db.session.delete(sender_inventory)
            db.session.commit()
            qrcode_in_db.qrcodetype = 'inventoryadd_app'
        else:
            print("inventoryadd_cash path")
            user = User.query.get(user_id)
            cash = int(item_id)
            if user.balance < cash:
                return jsonify({'error': 'Insufficient balance'}), 400
            if cash <= 0:
                return jsonify({'error': 'Insufficient balance'}), 400
            user.balance -= cash
            qrcode_in_db.qrcodetype = 'inventoryadd_cash'

        qrcode_in_db.targetid = item_id
        db.session.commit()
    return jsonify({"message":f"Item successfully loaded to shard."}), 200



def remove_user_from_all_nodes(user_id):
    """Remove a user from all nodes."""
    NodeUsers.query.filter_by(user_id=user_id).delete()
    db.session.commit()


