# combat.py
from database import MetUsers, Node, App, File, Inventory, User, NodeOperationsHistory, UserOrganization, db, NodeUsers, Bulletinboards, Posts, Network
from flask import url_for
import random
from sqlalchemy.sql.expression import func
from sqlalchemy.orm.attributes import flag_modified
from threading import Thread
import datetime as dt
from datetime import datetime, timedelta
import inspect
from ssecfg import sse_push

# seen = set()  # unused? check and delete


# debug function to check which function calls which.
def who_called_me(message):
    frame = inspect.currentframe()

    # Go back to the immediate caller frame
    caller_frame = frame.f_back

    # Go back one more frame to get the caller of the immediate caller
    grand_caller_frame = caller_frame.f_back
    if grand_caller_frame is None:  # This would mean we're at the top level, not inside a function
        grand_caller_name = "top level"
    else:
        grand_caller_name = grand_caller_frame.f_code.co_name

    print(f"********* {message} was called by {grand_caller_name} *********")


def setup_ic_scheduler(scheduler, app_instance):
    intervalSeconds = 2
    #slightly shake up intervals to minimize chances of them aligning in debug mode when two instances are started at the exact same time
    if app_instance.debug:
        intervalSeconds -= 0.3
        intervalSeconds += random.random()
        print("app is in debug mode, combat scheduler interval randomized to ", intervalSeconds)
    else:
        print("app is in production mode, combat scheduler interval set to", intervalSeconds)
    # Add the Black IC interaction processing job
    scheduler.add_job(
        id='ic_interaction_job',
        func=lambda: process_ic_interactions(app_instance),
        trigger='interval',
        seconds=intervalSeconds  # You can adjust the interval as needed
    )
    print("ic interaction scheduler set up")


def setup_restore_node_scheduler(scheduler, app_instance):
    scheduler.add_job(
        id='restore_cracked_nodes_job',
        func=lambda: restore_cracked_nodes(app_instance),
        trigger='interval',
        seconds=60  # You can adjust the interval as needed
    )
    print("restore cracked node scheduler set up")


def restore_cracked_nodes(flask_app):
    with flask_app.app_context():  # Push the application context
        # Get all cracked nodes
        cracked_nodes = Node.query.filter_by(is_cracked=True).all()

        print("waking up node restorer")
        # print("cracked nodes are", cracked_nodes)
        # Check if the crack timestamp is older than 60 minutes
        for node in cracked_nodes:
            if node.crack_timestamp and (
                    dt.datetime.utcnow() - node.crack_timestamp).total_seconds() > 3600:  # 3600 = 60 minutes * 60 seconds
                restore_node(node.id)
        # print("Trojan membership removal check")
        # Fetch all UserOrganization entries with endtime in the past
        expired_memberships = UserOrganization.query.filter(
            UserOrganization.endtime.isnot(None),
            UserOrganization.endtime < dt.datetime.utcnow()
        ).all()

        # Delete each expired membership
        for membership in expired_memberships:
            db.session.delete(membership)

        # Commit the changes to the database
        db.session.commit()

        # print(f"Removed {len(expired_memberships)} expired memberships.")


def same_organization_actions(node_id, node_type_name, app_id, app_type_name, is_cracked, user_id):
    print("same_organization_actions called")
    print("is_cracked: ", is_cracked)
    print("app_type_name: ", app_type_name)
    if is_cracked and app_type_name == "restore":
        print("restore use branch")
        restore_node(node_id)
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        return {"restore": node_id}

    if node_type_name in ["Account Info", "Intel"] and app_type_name == "firewall":
        print("same_organization_actions - Firewall")
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        crack_node(node_id)
        return {"firewall": node_id}

    if app_type_name == "sweep":
        print("same_organization_actions - Sweep")
        sweep(user_id)
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        return {"sweep": node_id}
    return {}


def different_organization_actions(node_id, node_type_name, app_id=None, app_type_enum=None, is_cracked=None,
                                   network_length=None, node_position=None, user_id=None, network_organization=None,
                                   second_app_id=None, second_app_type_name=None, attacker_id=None, citynet_number=None):

    print("different_organization_actions called")
    who_called_me("different_organization_actions")
    # Debug print lines for all received values
    # print("Debug - node_id:", node_id)
    # print("Debug - node_type_name:", node_type_name)
    # print("Debug - app_id:", app_id)
    # print("Debug - app_type_enum:", app_type_enum)
    # print("Debug - is_cracked:", is_cracked)
    # print("Debug - network_length:", network_length)
    # print("Debug - node_position:", node_position)
    # print("Debug - user_id:", user_id)
    # print("Debug - network_organization:", network_organization)
    # print("Debug - second_app_id:", second_app_id)
    # print("Debug - second_app_type_name:", second_app_type_name)

    node_user = NodeUsers.query.filter_by(user_id=user_id).first()
    
    print(is_cracked)
    if is_cracked:
        print("Node is already cracked, nothing to do")
        return {"message": "Node is already cracked, nothing to do"}
    
    if node_type_name == "Password" and app_type_enum == 'backdoor':
        print(f"Entered password node cracking branch for user {user_id}")
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        crack_node(node_id)
        return {"crack": node_id}

    elif node_type_name == "White IC":
        print(f"Entered White IC branch for user {user_id}")
        print(app_id)
        if app_id is not None:  # An app is being used
            if app_type_enum == 'attacker':
                print(f"White IC neutralized by user {user_id}")
                log_operation(node_id, user_id, 'app_use', app_id)
                log_app_usage(app_id)
                crack_node(node_id)
                node_user.interaction_data = None  # Clear interaction data
                return {"message": "White IC neutralized"}
            elif app_type_enum == 'cloak':
                print(f"White IC message stopped by user {user_id}")
                log_operation(node_id, user_id, 'app_use', app_id)
                log_app_usage(app_id)
                node_user.interaction_data = None  # Clear interaction data
                # No need to crack the node, just stopping the message
                return {"message": "Cloak active, White IC cancelled."}
        else:
            if not node_user.interaction_data:
                node_user.interaction_data = {
                        "entry_time": datetime.utcnow().isoformat(),
                        "used_apps": []
                    }
                db.session.commit()
            return {"message": "Entered White IC node."}

    elif node_type_name == "Grey IC":
        if app_type_enum == 'attacker':
            print(f"Grey IC neutralized by user {user_id}")
            log_operation(node_id, user_id, 'app_use', app_id)
            log_app_usage(app_id)
            crack_node(node_id)
            node_user.interaction_data = None  # Clear interaction data
            return {"message": "Grey IC neutralized"}
        else:
            if not node_user.interaction_data:
                node_user.interaction_data = {
                        "entry_time": datetime.utcnow().isoformat(),
                        "used_apps": []
                    }
                db.session.commit()
            return {"message": "Entered Grey IC node."}
    # here
    elif node_type_name == "Black IC":
        print("Black IC elif, in combat.py.different_organization_actions")
        print("app_type_enum: ", app_type_enum)
        print("************************************************************")

        # Fetch or create NodeUsers record
        
        if app_type_enum is None:
            if not node_user.interaction_data:
                node_user.interaction_data = {
                        "entry_time": datetime.utcnow().isoformat(),
                        "used_apps": []
                    }
                db.session.commit()
            return {"message": "Entered Black IC node."}

        used_apps = node_user.interaction_data.get("used_apps", [])
        print("Current used_apps:", used_apps)

        if app_type_enum and app_type_enum not in used_apps:
            print("Updating used_apps with:", app_type_enum)
            used_apps.append(app_type_enum)
            node_user.interaction_data["used_apps"] = used_apps
            flag_modified(NodeUsers, "interaction_data")
            db.session.flush()
            db.session.commit()
            print("Updated interaction_data committed:", node_user.interaction_data)

        # Check if both apps are used
        if set(used_apps) == {'attacker', 'defender'}:
            print("Both apps used on Black IC, processing...")
            crack_node(node_id)
            node_user.interaction_data = None  # Clear interaction data
            db.session.commit()
            print("Node cracked and interaction data cleared.")
            return {"message": "Black IC neutralized with both apps."}

        return {"message": f"App {app_type_enum} used on Black IC."}

        # Further processing is handled by APScheduler job

    elif node_type_name == "Account Info" and app_type_enum == 'siphon':
        print(f"Entered the Account Info and Siphon function for user {user_id}")
        print("network_organization: ", network_organization)
        print("citynet_number:", citynet_number)
        siphon_amount, siphon_target_citynet, siphon_receiver_citynet = siphon_funds(network_organization, citynet_number, user_id)

        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        crack_node(node_id)
        return {"siphon": (siphon_amount, siphon_target_citynet, siphon_receiver_citynet)}

    elif node_type_name == "Intel" and app_type_enum == 'crawler':
        print(f"Entered the Intel and Crawler function for user {user_id}")
        file_name = crawl_node(node_id, user_id)
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        crack_node(node_id)
        return {"crawl": file_name}

    elif is_cracked and app_type_enum == 'restore':
        print(f"Entered the Restore function for user {user_id} - in different_organization_actions???")
        restore_node(node_id)
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        return {"restore": node_id}

    elif app_type_enum == 'trojan' and node_position == network_length - 1:
        print(f"Entered the Trojan function for user {user_id}")
        print("user_id, network_id: ", user_id, network_organization)
        membership_duration = add_trojan_org_membership(user_id, network_organization)
        log_operation(node_id, user_id, 'app_use', app_id)
        log_app_usage(app_id)
        return {"trojan": membership_duration}

    else:
        return {}


def get_watchdog_user_for_org(organization_id):
    print("get_watchdog_user_for_org started, with organization_id: ", organization_id)
    user_orgs = UserOrganization.query.filter_by(organization_id=organization_id).all()

    for user_org in user_orgs:
        # Query the User table to get user details
        user = User.query.get(user_org.user_organization_id)
        if user and 'Architecture Watchdog' in user.username:
            print(f"Found User: {user.username}, User ID: {user.id}")
            return user.id  # Return the user ID immediately when a match is found

    # Print message and return None if no matching user is found
    print(f"No user found in organization with ID: {organization_id} containing 'Architecture Watchdog' in username")
    return None


def get_bulletin_board_for_org(organization_id):
    return Bulletinboards.query.filter_by(organization_id=organization_id).first()


def post_message_to_board(board_id, watchdog_user_id, message):
    print("post_message_to_board called")
    post = Posts(board_id=board_id, poster_id=watchdog_user_id, postcontent=message)
    print("post: ", post)
    db.session.add(post)
    db.session.commit()


def netrunner_vs_netrunner_actions(attacker_id, app_id, app_type_name, target_id):
    print("netrunner_vs_netrunner_actions finction kicked in")
    result = {}
    # Get the App type
    # app = App.query.get(app_id)
    # app_type_name = app.app_type.type

    # Check if target netrunner has Shield in their inventory
    second_app_id = has_shield(target_id)
    if second_app_id:
        # Block the attack and log the use of both apps
        result.update(block_attack(attacker_id, target_id))
        log_operation(None, attacker_id, 'app_use', app_id)
        log_operation(None, target_id, 'app_use', second_app_id)
        log_app_usage(app_id)
        log_app_usage(second_app_id)
    else:
        # Launch the attack and log the use of the attacker's app
        result.update(launch_attack(target_id, app_type_name))
        log_operation(None, attacker_id, 'app_use', app_id)
        log_app_usage(app_id)

    return result


def generate_trojan_membership_duration():
    """
    Generate a random INT number between 120 - 240 (minutes) for Trojan usage
    """
    return random.randint(120, 240)


def add_trojan_org_membership(user_id, network_organization):
    # Calculate the endtime for the membership
    membership_duration = generate_trojan_membership_duration()
    endtime = datetime.utcnow() + timedelta(minutes=membership_duration)

    # Create a new UserOrganization entry
    new_membership = UserOrganization(
        user_organization_id=user_id,
        organization_id=network_organization,
        endtime=endtime
    )

    # Add the new membership to the database session and commit
    db.session.add(new_membership)
    db.session.commit()

    # Return the duration of the membership for further use
    return membership_duration


def check_interaction(node_id, node_type_name, app_id=None, app_type_name=None, app_type_enum=None, is_cracked=None,
                      network_organization=None, netrunner_organizations=None, network_length=None, node_position=None,
                      attacker_id=None, user_id=None, target_id=None, second_app_id=None, second_app_type_name=None, citynet_number=None):
    who_called_me("check_interaction")
    print("Beginnig of check_interaction debug print block")
    # print("Debug - node_id:", node_id)
    print("Debug - node_type_name:", node_type_name)
    # print("Debug - app_id:", app_id)
    print("Debug - app_type_name:", app_type_name)
    print("Debug - is_cracked:", is_cracked)
    # print("Debug - network_organization:", network_organization)
    # print("Debug - netrunner_organizations:", netrunner_organizations)
    # print("Debug - network_length:", network_length)
    # print("Debug - node_position:", node_position)
    # print("Debug - attacker_id:", attacker_id)
    # print("Debug - target_id:", target_id)
    # print("Debug - second_app_id:", second_app_id)
    # print("Debug - second_app_type_name:", second_app_type_name)
    # print("End check_interaction debug print block")
    print("****************")

    result = {}
    if app_id is None:
        # Handle the logic for no app case
        # e.g. result.update(handle_no_app_action(node_id, node_type_name, user_id, network_organization))
        print("No app_id, so this is a default node action case")
        if network_organization in netrunner_organizations:
            print("netrunner and network organization match, friendly visitor, no actions from nodes")
        else:
            print("Diff org action call")
            result.update(different_organization_actions(node_id, node_type_name, app_id, app_type_enum,
                                                         is_cracked, network_length, node_position,
                                                         user_id, network_organization, second_app_id, second_app_type_name, attacker_id, citynet_number))
    else:
        # Check the interactions based on organization
        print("app_id provided: Check the interactions based on organization")
        if network_organization in netrunner_organizations:
            print("friendly user redirection to same_organization_actions")
            result.update(same_organization_actions(node_id, node_type_name, app_id, app_type_name,
                                                    is_cracked, attacker_id))
        else:
            print("hostile user redirection to different_organization_actions")
            result.update(different_organization_actions(node_id, node_type_name, app_id, app_type_enum,
                                                         is_cracked, network_length, node_position,
                                                         user_id, network_organization, second_app_id, second_app_type_name, attacker_id, citynet_number))

        # Check the interactions between netrunners if applicable
        if target_id:
            print("Target ID provided, this is a netrunner_vs_netrunner_actions redirect")
            result.update(netrunner_vs_netrunner_actions(attacker_id, app_id, target_id))
    print("result at the end of check_interaction : ", result)
    return result


def log_operation(node_id, user_id, operation_type, app_id=None):
    """
    Log the operation to the NodeOperationsHistory table.
    """
    new_operation = NodeOperationsHistory(
        node_id=node_id,
        user_id=user_id,
        operation_type=operation_type,
        timestamp=dt.datetime.utcnow(),
        app_used=app_id
    )
    node_users = NodeUsers.query.filter_by(node_id=node_id).all()
    for nu in node_users:
        sse_push(nu.user_id, operation_type, {
                                    'user_id': user_id,
                                    'app_used': app_id
                                })
    db.session.add(new_operation)
    db.session.commit()


def log_app_usage(app_id):
    """
    Set the app's use_timestamp to current date and time.
    """
    selected_app = App.query.get(app_id)
    selected_app.use_timestamp = dt.datetime.utcnow()
    print("************** App usage logged! ***************")
    db.session.commit()


def crack_node(node_id):
    """
    Mark a node as cracked.
    """
    node = Node.query.get(node_id)
    node.is_cracked = True
    node.crack_timestamp = dt.datetime.utcnow()  # Set the crack timestamp
    db.session.add(node)  # Explicitly add the node to the session
    db.session.commit()

    # send a crack event
    node_users = NodeUsers.query.filter_by(node_id=node_id).all()
    for nu in node_users:
        sse_push(nu.user_id, 'node_cracked', {
                                    'node_id': node_id
                                })


def restore_node(node_id):
    print("restore_node called for node: ", node_id)
    """
    Restore a node to full functionality.
    """
    node = Node.query.get(node_id)
    node.is_cracked = False
    node.crack_timestamp = None  # Clear crack_timestamp
    db.session.add(node)  # Explicitly add the node to the session
    db.session.commit()

    # send a restore event
    node_users = NodeUsers.query.filter_by(node_id=node_id).all()
    for nu in node_users:
        sse_push(nu.user_id, 'node_restored', {
                                    'node_id': node_id
                                })


def hurt_user(user_id, severity=None):
    who_called_me("hurt_user")
    user = User.query.get(user_id)
    print("User previous health status: ", user.wound)

    if user is None:
        print(f"User with ID {user_id} not found.")
        return  # Handle user not found

    if severity is None or severity == "wounded":
        print("severity is None")
        # Incremental worsening of health status
        if user.wound == "unhurt":
            user.wound = "wounded"
        elif user.wound == "wounded":
            user.wound = "dying"
        elif user.wound == "dying":
            user.wound = "dead"

    elif severity == "dying":
        # set to dying unless already dying, then kill
        if user.wound == "unhurt":
            user.wound = "dying"
        elif user.wound == "wounded":
            user.wound = "dying"
        elif user.wound == "dying":
            user.wound = "dead"
        user.wound = severity
    else:
        print(f"Invalid severity level: {severity}")
        return user.wound # Handle invalid severity level

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error updating user {user_id}: {e}")

    return user.wound


def siphon_funds(network_organization, citynet_number, user_id):
    print("network_organization in siphon: ", network_organization)
    print("citynet_number in siphon: ", citynet_number)
    print("user_id in siphon: ", user_id)

    # Get a random user from the organization
    user_org = UserOrganization.query.filter_by(organization_id=network_organization).order_by(func.rand()).first()
    print("user_org: ", user_org)

    if not user_org:
        # Handle the case where no user is associated with the organization
        print("No users in this org.")
        return None, None, None

    # Find the target user from whom the amount will be siphoned
    target_user = User.query.get(user_org.user_organization_id)
    print("target_user: ", target_user)

    # Siphon a random percentage (10-30%) of their balance
    siphon_percentage = random.randint(10, 30) / 100.0
    siphoned_amount = int(target_user.balance * siphon_percentage)

    # Deduct the siphoned amount from the target user's balance
    target_user.balance -= siphoned_amount
    print("deducted")

    # Identify the receiver user
    if citynet_number.lower() == 'self':
        receiver_user = User.query.get(user_id)
        print("receiver_user from user_id: ", receiver_user)
    else:
        receiver_user = User.query.filter_by(citynet=citynet_number).first()
        print("receiver_user from citynet: ", receiver_user)

    if not receiver_user:
        print("Receiver user not found.")
        return None, None, None

    # Add the siphoned amount to the receiver user's balance
    receiver_user.balance += siphoned_amount
    print("added")

    db.session.commit()

    return siphoned_amount, target_user.citynet, receiver_user.citynet


def crawl_node(node_id, user_id):
    node = Node.query.get(node_id)
    if not node.file_ids:
        return "No files in this node."

    # Select a random file ID from the node's file_ids list
    random_file_id = random.choice(node.file_ids)

    # Fetch the file using the selected file ID
    file = File.query.get(random_file_id)

    # Check if the user already has this file
    existing_file = Inventory.query.filter_by(user_id=user_id, file_id=file.id).first()
    if existing_file:
        return "File already in inventory."

    # Add the file to the user's inventory
    inventory = Inventory(user_id=user_id, file_id=file.id)
    db.session.add(inventory)
    db.session.commit()

    return file.name


def has_shield(user_id):
    user = User.query.get(user_id)
    for inventory_item in user.inventories:
        if inventory_item.app and inventory_item.app.app_type.type == 'shield':
            return inventory_item.app.id
    return None


def delete_random_app(target_id):
    user = User.query.get(target_id)
    if user is None:
        # Handle the case when the user is not found
        return {"target_message": "User not found"}

    apps = [inventory_item.app for inventory_item in user.inventories if inventory_item.app and inventory_item.app.use_timestamp is None]

    print("apps: ", apps)
    if apps:
        random_app = random.choice(apps)
        log_app_usage(random_app.id)
        target_message = f"{random_app.name}"
        operation_type = "appdelete"
        sse_push(user.id, operation_type, {'app_deleted': random_app.name})
        return {"target_message": target_message}
    return {}


def kick_user_from_network(target_id):
    node_user = NodeUsers.query.filter_by(user_id=target_id).first()
    if node_user:
        network_name = node_user.node.network_name  # This line assumes there is a network_name attribute
        db.session.delete(node_user)
        db.session.commit()
        target_message = f"You got kicked out from the {network_name} network."
        attacker_message = f"You just kicked user with id {target_id} from this network."
        return {"attacker_message": attacker_message, "target_message": target_message}
    return {}


def launch_attack(target_id, app_type_name):
    result = {}
    if app_type_name == "Sword":
        # Delete one random app from target user
        result.update(delete_random_app(target_id))
    elif app_type_name == "Banhammer":
        # Kick target user from the network
        result.update(kick_user_from_network(target_id))
    elif app_type_name == "Zap":
        # Hurt the target user
        hurt_user(target_id)
        result["message"] = "Your Zap app hurt the target user!"
    return result


def block_attack(attacker_id, target_id):
    return {
        "attacker_message": "Your attack was blocked!",
        "target_message": "You were attacked, but your Shield protected you!"
    }


# Start the background task
def start_restore_thread(flask_app):
    # print("started restore thread")
    restore_thread = Thread(target=restore_cracked_nodes, args=(flask_app,))
    restore_thread.daemon = True
    restore_thread.start()


def sweep(user_id):
    # 1. Identify the User’s Organization
    current_membership = UserOrganization.query.filter(
        UserOrganization.user_organization_id == user_id,
        UserOrganization.endtime.is_(None)
    ).first()

    if current_membership:
        organization_id = current_membership.organization_id

        # 2. Find Temporary Memberships
        temporary_memberships = UserOrganization.query.filter(
            UserOrganization.organization_id == organization_id,
            UserOrganization.endtime.isnot(None)  # Filtering where endtime is not None
        ).all()

        # 3. Delete Temporary Memberships
        for membership in temporary_memberships:
            db.session.delete(membership)

        db.session.commit()


def white_ic_alert(user_id, network_id):
    user = User.query.get(user_id)
    network = Network.query.get(network_id)
    if user:
        intruder_info = f"Handle: {user.username} (CityNet: {user.citynet})"
        watchdog_user = get_watchdog_user_for_org(network.organization_id)
        if watchdog_user:
            board = get_bulletin_board_for_org(network.organization_id)
            if board:
                message = f"Intruder detected in your network! {intruder_info}."
                post_message_to_board(board.id, watchdog_user, message)


def process_ic_interactions(app_instance):
    # print("Processing IC interactions for all networks...")
    current_time = datetime.utcnow()

    with app_instance.app_context():
        node_users = NodeUsers.query.with_for_update(of=NodeUsers).all()
        for nu in node_users:
            if nu.attack_data:
                attack_time = datetime.fromisoformat(nu.attack_data.get("time"))
                time_diff = current_time - attack_time
                if time_diff.total_seconds() > 15: #this is a safe timeout limit, 5 sec for decision + network overhead
                    # a little roundabout way of locking one row at a time
                    attackNu = NodeUsers.query.with_for_update(of=NodeUsers).filter_by(id=nu.id).first()
                    if attackNu.attack_data: # re-check to avoid doubling
                        appTypeName = attackNu.attack_data.get("app")
                        targetId = attackNu.attack_data.get("target")
                        print("pvp app hit from", nu.user_id, "to", targetId)
                        attackNu.attack_data = None
                        db.session.commit()
                        if hasattr(targetId, '__len__') and (not isinstance(targetId, str)):
                            for target in targetId:
                                pvp_app_hit(appTypeName, attackNu.node_id, target, attackNu.user_id)
                        else:
                            pvp_app_hit(appTypeName, attackNu.node_id, targetId, attackNu.user_id)

            if nu.interaction_data:       
                entry_time = datetime.fromisoformat(nu.interaction_data.get("entry_time"))
                used_apps = nu.interaction_data.get("used_apps", [])
                time_diff = current_time - entry_time
                if time_diff.total_seconds() > 30:  # overall 30sec timeouts will save us db interactions
                    # a little roundabout way of locking one row at a time
                    icNu = NodeUsers.query.with_for_update(of=NodeUsers).filter_by(id=nu.id).first()
                    if icNu.interaction_data: # re-check to avoid doubling
                        icNu.interaction_data = None  # clear interaction data immediately to avoid threading duplicates
                        db.session.commit()
                        node = Node.query.get(icNu.node_id)
                        if node.node_type.name == "Black IC":
                            if set(used_apps) == {'attacker', 'defender'} or node.is_cracked:
                                # Already handled immediately in different_organization_actions
                                pass
                            elif 'attacker' in used_apps or 'defender' in used_apps:
                                # User is wounded
                                newState = hurt_user(icNu.user_id)
                                sse_push(icNu.user_id, 'black_ic_hit', {
                                    'state': newState
                                })
                            else:
                                # User is dying
                                newState = hurt_user(icNu.user_id, "dying")
                                sse_push(icNu.user_id, 'black_ic_hit', {
                                    'state': newState
                                })
                        elif node.node_type.name == "Grey IC":
                            if 'attacker' in used_apps or node.is_cracked:
                                pass
                            else:
                                delete_random_app(icNu.user_id)
                                sse_push(icNu.user_id, 'grey_ic_hit', {})
                                print(f"Grey IC deleted an app from user {icNu.user_id} due to no attacker app used in time.")
                            
                        elif node.node_type.name == "White IC":
                            if 'attacker' in used_apps or 'cloak' in used_apps or node.is_cracked:
                                # Already handled immediately in different_organization_actions
                                pass
                            else:
                                print("No app used, or the app used is not an attacker or cloak against White IC")
                                white_ic_alert(icNu.user_id, node.network_id)
                                sse_push(icNu.user_id, 'white_ic_hit', {})

def pvp_app_hit(appTypeName, nodeId, userId, attackerId):
    match appTypeName:
        case "Banhammer":
            print("banhammer hit")
            messageDict = leave_network(userId)
            messageDict["message"] = "You have been forcibly ejected from this network!"
            messageDict["attacker"] = attackerId
            messageDict["app"] = appTypeName
            sse_push(userId, "pvp_hit", messageDict)
        case "Sword":
            print ("sword hit")
            message = delete_random_app(userId).get("target_message")
            sse_push(userId, "pvp_hit", {"attacker":attackerId, "app":appTypeName, "message":message})
        case "Zap":
            print ("zap hit")
            newState = hurt_user(userId)
            sse_push(userId, "pvp_hit", {"attacker":attackerId, "app":appTypeName, "state":newState})
        case "Tracer":
            print ("tracer hit")
            tracer_hit(userId, attackerId)
            sse_push(userId, "pvp_hit", {"attacker":attackerId, "app":appTypeName})
        case _:
            print ("unknown app")
            return
    sse_push(attackerId, "pvp_result", {"app":appTypeName, "target":userId, "success":1})

def tracer_hit(user_id, attacker_id):
    print("tracer hit by",attacker_id,"against",user_id)
    met_user_entry = MetUsers.query.filter_by(
                    user_id=attacker_id,
                    met_user_id=user_id
        ).first()
    print("met_user_entry: ", met_user_entry)

    if met_user_entry:
        met_user_entry.tracer_used = True
        # Fetch CityNet number of the met user
        user = User.query.filter_by(id=user_id).first()
        met_user_citynet_number = user.citynet

        # Update citynet_number
        met_user_entry.citynet_number = met_user_citynet_number
        met_user_entry.tracer_used = True

        db.session.commit()  # Commit the changes to the database
        sse_push(attacker_id, "tracer_success", {"user_id":user_id, "citynet":met_user_citynet_number, "username":user.username})
        print("tracer used set and citynet_number updated")

def leave_network(user_id):
    # Log the start of the function
    print("leave_network function called")
    # Get the user's ID from the session
    print("leave_network for user_id: ", user_id)

    # Get the user's current node association before any deletions
    node_associations = NodeUsers.query.filter_by(user_id=user_id).all()
    print("leave_network User's node association before deletion:", node_associations)

    if len(node_associations) > 1:
        print("There were multiple node associations for the user. This is probably erroneous but this is the best time to clean it up.")
    elif len(node_associations) == 0:
        print("User was not associated with any node!")
        return {
            "status": "success",
            "message": "Successfully exited the network",
            "redirect": url_for('user_app.scanner_redirect')
        }
    
    networkId = Node.query.get(node_associations[0].node_id).network_id
    
    # If the user is currently associated with a node
    for current_node_association in node_associations:
        # Log the user's exit operation for the current node
        new_operation = NodeOperationsHistory(
            node_id=current_node_association.node_id,
            user_id=user_id,
            operation_type='logout',
            timestamp=datetime.now()
        )
        db.session.add(new_operation)
        db.session.commit()
        # Notify other users that the current user has left the current node
        sse_push(user_id, 'leave_node', {'node_id': current_node_association.node_id})

    # Remove the user's entry from the NodeUsers table
    print("Exit network esetén node user delete")
    NodeUsers.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    # Notifying other users via the database
    met_users_query = db.session.query(MetUsers.met_user_id).filter(MetUsers.user_id == user_id)
    met_users = [user.met_user_id for user in met_users_query]

    # Notify each met user
    for u_id in met_users:
        print("exit netwotk - Notify each met user")

        # Pass the CityNet number (or another identifier) to the client
        sse_push(u_id, 'user_left_network', {
            'user_id': user_id,
        })

    # Remove the user's met_users entries from the database
    MetUsers.query.filter((MetUsers.user_id == user_id) | (MetUsers.met_user_id == user_id)).delete()
    print("met users entries deleted")
    # Commit all the changes to the database
    db.session.commit()

    update_met_users(networkId)
    # print("exit network, met users removal committed to db")
   
    # Return a success message and redirect the user to the scanner page
    return {
        "status": "success",
        "message": "Successfully exited the network",
        "redirect": url_for('user_app.scanner_redirect')
    }

def update_met_users(network_id):
    # Get all users in the network
    users_in_network = User.query.join(NodeUsers, User.id == NodeUsers.user_id).join(Node, Node.id == NodeUsers.node_id).filter(Node.network_id == network_id).all()

    for user in users_in_network:
        # Initialize the data structure
        met_users_data = {network_id: {user.id: {"met_users": {}}}}

        # Fetch updated met_users data for this user
        updated_met_users = MetUsers.query.filter_by(user_id=user.id).all()

        for met_user in updated_met_users:
            met_user_data = {
                "tracer_used": met_user.tracer_used,
                "citynet_number": met_user.citynet_number,
                "current_location": {
                    "node_name": met_user.current_node_name,
                    "order": met_user.current_order
                }
            }
            met_users_data[network_id][user.id]["met_users"][met_user.met_user_id] = met_user_data

        # Send an SSE push message with the updated met users data
        sse_push(user.id, 'update_met_users', met_users_data)