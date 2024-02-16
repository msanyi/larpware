# netrunning.py
from flask import Blueprint, render_template, request, url_for, flash, session, jsonify
from combat import check_interaction, delete_random_app, white_ic_alert, pvp_app_hit, leave_network, update_met_users
from database import User, Network, Organizations, NodeType, Node, App, Inventory, AppType, db, NodeOperationsHistory, NodeUsers, MetUsers, UserOrganization, File
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
from ssecfg import sse_push
from ssecfg import client_manager
import serializer_helpers
import datetime as dt
from datetime import datetime, timezone, timedelta
import inspect
from navbar import NavBarInfo
from healthmonitor import get_display_state


netrunning_blueprint = Blueprint('netrunning', __name__)
seen = set()


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


@netrunning_blueprint.route('/get_applicable_apps', methods=['GET'])
def get_applicable_apps_endpoint():
    node_id = request.args.get('node_id')
    user_id = session['user_id']
    applicable_apps = get_applicable_inventory_apps(node_id, user_id)
    return jsonify(applicable_apps)


@netrunning_blueprint.route('/netrunning')
def netrunning():
    # who_called_me("netrunning_blueprint.netrunning")

    user_id = session['user_id']
    current_node = get_current_node(user_id)
    node, is_starting_game = get_node_from_request_or_default(current_node, user_id)
    print("current_node id in netrunning function: ", current_node.id)

    if node is None:
        node = handle_missing_node(is_starting_game, user_id)

    network, current_user, is_trojan_planted = get_network_user_and_trojan_status(node, user_id)
    organization, node_type, users_in_node, next_node, prev_node, user_organizations, current_qrcode, is_cracked = get_additional_data(node, user_id, network)
    met_users_dict = get_met_users(network.id, user_id)

    print("is_cracked value, before calling compile_data: ", is_cracked)
    data = compile_data(
        network, organization, node, node_type, users_in_node,
        next_node, prev_node, session['user_id'], user_organizations,
        current_qrcode, met_users_dict, is_trojan_planted, current_user, is_cracked
    )
    # print("data id in netrunning function: ", data)
    user = User.query.filter_by(id=user_id).first()
    health_state = user.wound
    display_state = get_display_state(health_state)
    print(" BEGIN print all session data from netrunning function ------------------")
    for key in session:
        print(f"{key}: {session[key]}")
    print(" END print all session data from netrunning function ------------------")
    return render_template('netrunning.html', data=data, headerinfo=NavBarInfo(), health=health_state, display_state=display_state)


def get_current_node(user_id):
    # who_called_me("get_current_node")
    # print(f"Input data: user_id={user_id}")
    current_node = Node.query.join(NodeUsers, Node.id == NodeUsers.node_id).filter(NodeUsers.user_id == user_id).first()
    # print(f"Output data: current_node={current_node}")
    return current_node


def get_node_from_request_or_default(current_node, user_id):
    # who_called_me("get_node_from_request_or_default")
    print(f"Input data in get_node_from_request_or_default function: current_node={current_node}, user_id={user_id}")
    node_id = request.args.get('node_id')
    is_starting_game = False

    if node_id:
        print("get_node_from_request_or_default - is_starting_game is False")
        node = Node.query.get(node_id)
        if current_node:
            print("get_node_from_request_or_default: node_user_management called with user_id, current_node.id, node.id: ", user_id, current_node.id, node.id)
            node_user_management(user_id, current_node.id, node.id)
    else:
        is_starting_game = True
        print("get_node_from_request_or_default - is_starting_game is True")
        node = current_node
        if node and node.order == 0:
            print("get_node_from_request_or_default: node_user_management called with user_id, current_node.id = None, node.id: ", user_id, node.id)
            node_user_management(user_id, None, node.id)

    print(f"Output data from get_node_from_request_or_default function: node={node}, is_starting_game={is_starting_game}")
    return node, is_starting_game


def handle_missing_node(is_starting_game, user_id):
    # who_called_me("handle_missing_node")
    # print(f"Input data: is_starting_game={is_starting_game}, user_id={user_id}")
    if is_starting_game:
        first_node = Node.query.filter_by(network_id=Network.id, order=0).first()
        if first_node:
            new_node_user = NodeUsers(user_id=user_id, node_id=first_node.id)
            db.session.add(new_node_user)
            db.session.commit()
            node = first_node
        else:
            node = None
    else:
        node = None

    # print(f"Output data: node={node}")
    return node


def get_network_user_and_trojan_status(node, user_id):
    # who_called_me("get_network_user_and_trojan_status")
    # print(f"Input data: node={node}, user_id={user_id}")
    network = Network.query.get(node.network_id)
    current_user = User.query.get(user_id)
    is_trojan_planted = False

    if node.order == len(network.nodes.all()) - 1:
        current_membership = UserOrganization.query.filter_by(
            user_organization_id=current_user.id,
            endtime=None
        ).first()

        if current_membership:
            organization_id = current_membership.organization_id
            trojan_memberships = UserOrganization.query.filter(
                UserOrganization.organization_id == organization_id,
                UserOrganization.user_organization_id != current_user.id,
                UserOrganization.endtime.isnot(None),
                UserOrganization.endtime > datetime.utcnow()
            ).all()

            is_trojan_planted = bool(trojan_memberships)

    # print(f"Output data: network={network}, current_user={current_user}, is_trojan_planted={is_trojan_planted}")
    return network, current_user, is_trojan_planted


def get_additional_data(node, user_id, network):
    # who_called_me("get_additional_data")
    print(f"Input data for get_additional_data: node={node}, user_id={user_id}, network={network}")

    organization = Organizations.query.get(network.organization_id)
    node_type = NodeType.query.get(node.node_type_id)
    users_in_node = User.query.join(NodeUsers, User.id == NodeUsers.user_id).filter(NodeUsers.node_id == node.id).all()
    next_node = Node.query.filter(Node.network_id == network.id, Node.order == node.order + 1).one_or_none()
    prev_node = Node.query.filter(Node.network_id == network.id, Node.order == node.order - 1).one_or_none()
    # inventory_apps = App.query.join(Inventory, App.id == Inventory.app_id).filter(Inventory.user_id == user_id).all()
    user_organizations = UserOrganization.query.filter_by(user_organization_id=user_id).all()
    current_qrcode = session.get('current_qrcode', None)
    is_cracked = node.is_cracked

    print(f"Output data from get_additional_data: organization={organization}, node_type={node_type}, users_in_node={users_in_node}, next_node={next_node}, prev_node={prev_node}, inventory_apps (listed correctly), user_organizations={user_organizations}, current_qrcode={current_qrcode}, is_cracked ={is_cracked}")
    return organization, node_type, users_in_node, next_node, prev_node, user_organizations, current_qrcode, is_cracked


def get_met_users(network_id, user_id):
    # Initialize the data structure
    met_users_data = {network_id: {user_id: {"met_users": {}}}}
    met_users = MetUsers.query.filter_by(user_id=user_id).all()

    for met_user in met_users:
        met_user_data = {
            "tracer_used": met_user.tracer_used,
            "citynet_number": met_user.citynet_number,
            "current_location": {
                "node_name": met_user.current_node_name,
                "order": met_user.current_order
            }
        }
        met_users_data[network_id][user_id]["met_users"][met_user.met_user_id] = met_user_data

    return met_users_data

def compile_data(network, organization, node, node_type, users_in_node, next_node, prev_node, user_id, user_organizations, qrcode, met_users_dict, is_trojan_planted, current_user, is_cracked):
    # who_called_me("compile_data")
    # print(f"Input data: network={network}, organization={organization}, node={node}, node_type={node_type}, users_in_node={users_in_node}, next_node={next_node}, prev_node={prev_node}, inventory_apps (correct list of apps, long), user_id={user_id}, user_organizations={user_organizations}, qrcode={qrcode}, met_users_dict={met_users_dict}, is_trojan_planted={is_trojan_planted}, current_user={current_user}")
    user_organization_ids = [serializer_helpers.user_organization_to_dict(org) for org in user_organizations]
    # print("user_organization_ids: ", user_organization_ids)

    # Get the Network instance based on network_id
    print("compile_data function, network: ", network)
    print("compile_data function, is_cracked: ", is_cracked)
    # Get the organization_id of the network
    network_org_id = network.organization_id

    # Query UserOrganization for all organizations associated with the user
    user_orgs = UserOrganization.query.filter_by(user_organization_id=user_id).all()

    # Check if any of the user's organizations match the network's organization
    is_home_user = any(org.organization_id == network_org_id for org in user_orgs)

    print("is_home_user: ", is_home_user)

    data = {
        'network': serializer_helpers.network_to_dict(network),
        'organization': serializer_helpers.organization_to_dict(organization),
        'node': serializer_helpers.node_to_dict(node),
        'node_type': serializer_helpers.node_type_to_dict(node_type),
        'users_in_node': [serializer_helpers.user_to_dict(user) for user in users_in_node],
        'next_node_id': None if next_node is None else next_node.id,
        'prev_node_id': None if prev_node is None else prev_node.id,
        # 'inventory_apps': [serializer_helpers.app_to_dict(app) for app in inventory_apps],
        'user_id': user_id,
        'user_organization_ids': user_organization_ids,
        'node_id': node.id,
        'qrcode': qrcode,
        'met_users_dict': met_users_dict,
        'node_description': node_type.description,
        'server_messages': session.get("server_messages", None),
        'cloak_data': session.get("cloak_data", None),
        'is_trojan_planted': is_trojan_planted,
        'user_dict': serializer_helpers.user_to_dict(current_user),
        'is_home_user': is_home_user,
        'is_cracked': is_cracked
    }

    # print(f"************************************************** Output data: data={data}")
    return data


# Displaying node actions
@netrunning_blueprint.route('/display_node_actions', methods=['GET'])
def display_node_actions():
    node_id = request.args.get('node_id')
    node = Node.query.get(node_id)

    if node:
        user_id = session['user_id']
        user = User.query.get(user_id)
        network = Network.query.get(node.network_id)
        organization = Organizations.query.get(network.organization_id)
        node_type = NodeType.query.get(node.node_type_id)
        is_cracked = node.is_cracked

        allowed_app_types = node_type.apps

        # Filter the allowed actions based on the conditions
        actions = []
        for app_type in allowed_app_types:
            if organization.id not in [org.id for org in user.organizations] and app_type.name == "Backdoor" and not is_cracked:
                actions.append({"app_type": app_type.name, "interaction": node_type.interaction})
            elif organization.id in [org.id for org in user.organizations] and app_type.name == "Restore" and is_cracked:
                actions.append({"app_type": app_type.name, "interaction": node_type.interaction})

        return jsonify(actions)
    else:
        return jsonify({"status": "error", "message": "Node not found"})


# Using apps in inventory
@netrunning_blueprint.route('/use_app', methods=['POST'])
def use_app():
    who_called_me("use_app")
    print("use_app function called**********")
    app_type_name = request.form.get('app_type_name')  # Get the app type name
    node_id = request.form.get('node_id')
    user_id = session['user_id']
    second_app_id = request.form.get('second_app_id', None)  # Optional second app (e.g., Shield)
    citynet_number = request.form.get('citynet_number', None)  # Fetch the CityNet number from the request

    # Fetch the app type
    app_type = AppType.query.filter_by(name=app_type_name).first()
    if app_type is None:
        return jsonify({"status": "error", "message": "App type not found"})

    # Fetch the first UNUSED app of the specified type from the user's inventory
    inventory_app = Inventory.query.join(App, Inventory.app_id == App.id).filter(
        Inventory.user_id == user_id, App.app_type_id == app_type.id, App.use_timestamp.is_(None)
    ).first()
    if inventory_app is None or inventory_app.app is None:
        return jsonify({"status": "error", "message": "App not found"})

    # Check if the app is Tracer
    if app_type_name.lower() == 'tracer':
        print("inventory_app id: ", inventory_app.id)
        return use_tracer(user_id, node_id)

    netrunner_app = inventory_app.app

    # Fetch necessary objects
    node = Node.query.get(node_id)
    user = User.query.get(user_id)
    network = Network.query.get(node.network_id)
    organization = Organizations.query.get(network.organization_id)
    node_type = NodeType.query.get(node.node_type_id)
    netrunner_organizations = [org.organization_id for org in user.organizations]

    # Calculate network length by counting nodes
    network_length = len(network.nodes.all())

    # Check if the app is found
    if netrunner_app is None:  # Check if app is None
        return jsonify({"status": "error", "message": "App not found"})

    # Check if the app is already used
    if netrunner_app.use_timestamp:
        return jsonify({"status": "error", "message": "App has already been used"})

    # Check if the app is applicable for the node
    if netrunner_app.app_type_id not in [app_type.id for app_type in node_type.apps]:
        return jsonify({"status": "error", "message": "App is not applicable for this node"})

    # Check if the second app is provided and fetch its type
    second_app_type_name = None
    if second_app_id:
        second_app = App.query.get(second_app_id)
        second_app_type_name = second_app.app_type.type

    session["cloak_data"] = {
        # user_id: {"node_id": node_id, "timestamp": timestamp}
    }

    # Determine the interaction based on organization and other factors
    result = check_interaction(
        node_id=node.id,
        node_type_name=node_type.name,
        app_id=netrunner_app.id,
        app_type_name=netrunner_app.app_type.type,
        app_type_enum=netrunner_app.app_type.type,  # Added this line
        is_cracked=node.is_cracked,
        network_organization=organization.id,
        netrunner_organizations=netrunner_organizations,
        network_length=network_length,
        node_position=node.order,
        attacker_id=user.id,
        user_id=user.id,  # Added this line
        second_app_id=second_app_id,
        second_app_type_name=second_app_type_name,
        citynet_number=citynet_number
    )
    print("Result: ", result)
    if result.get("message") == "Cloak active, White IC cancelled.":
        user_message = "Successfully Cloaked against White IC. Time remaining: "
        user_cloak_data = {
            "node_id": node.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": user_message
        }
        session["cloak_data"] = {user_id: user_cloak_data}

    # session_check
    session_check = session["cloak_data"]
    # print("session_check: ", session_check)

    # Mark the app as used
    netrunner_app.use_timestamp = datetime.utcnow()
    db.session.commit()

    # Log the node action
    node_operation = NodeOperationsHistory(
        node_id=node_id,
        user_id=user_id,
        operation_type='app_use',
        timestamp=datetime.utcnow(),
        app_used=netrunner_app.id
    )
    if app_type_name.lower() == "siphon" and citynet_number:
        print("use_app siphon branch")
        if citynet_number == "self":
            print("siphon target:self")
            user.balance += result.get('siphoned_amount', 0)
        else:
            target_user = User.query.filter_by(citynet=citynet_number).first()
            print("siphon target_user", target_user)
            if target_user:
                target_user.balance += result.get('siphoned_amount', 0)
        db.session.commit()
    db.session.add(node_operation)
    db.session.commit()

    sse_push(user_id, 'app_used', {
        'node_id': node_id,
        'user_id': user_id
    })
    print("use_app sse:push called: app_used")

    sse_push(user_id, 'app_used_update', {
        'node_id': node_id,
        'user_id': user_id,
        'node_status': "cracked" if node.is_cracked else "good",
        'is_cracked': node.is_cracked,
        'inventory_apps': get_applicable_inventory_apps(node_id, user_id),
        'node_type_id': node.node_type_id,
        'cloak_data': user_cloak_data if 'user_cloak_data' in locals() else None
    })
    print("************************************** use_app sse:push called: app_used_update")
    # Notify other netrunners who have met this user using database
    met_users_query = db.session.query(MetUsers.met_user_id).filter(MetUsers.network_id == network.id, MetUsers.user_id == user_id)
    met_users = [user.met_user_id for user in met_users_query]
    # print("met_users in use_app, Notify other netrunners who have met this user using database: ", met_users)

    for other_user_id in met_users:
        sse_push(other_user_id, 'user_interaction', {'node_id': node_id, 'user_id': user_id, 'action': 'used_app', 'app_name': app_type_name})
        print("use_app sse:push called: other_user_id, user_interaction")
    return jsonify({"status": "success", "message": "App used", "result": result})


@netrunning_blueprint.route('/exit_network', methods=['POST'])
def exit_network():
    # Log the start of the function
    print("exit_network function called")
    # Get the user's ID from the session
    user_id = session['user_id']
    session.pop('current_qrcode', None)

    if not session.get('logged_in'):
        print("exit network: user is not logged_in???")
        return jsonify({"status": "error", "message": "Not logged in"})

    resultDict = leave_network(user_id)

    return jsonify(resultDict)


def get_applicable_inventory_apps(node_id, user_id):
    # print("get_applicable_inventory_apps called")
    node = Node.query.get(node_id)
    other_users_in_node = [nodeuser.id for nodeuser in NodeUsers.query.filter(NodeUsers.node_id == node_id, NodeUsers.user_id != user_id).all()]
    user = User.query.get(user_id)
    network = Network.query.get(node.network_id)
    node_type = NodeType.query.get(node.node_type_id)
    is_cracked = node.is_cracked
    user_organization_ids = [org.organization_id for org in user.organizations]
    is_home_network = network.organization_id in user_organization_ids

    # Get the allowed app types for this node
    allowed_app_types = node_type.apps
    applicable_app_types = []

    # print("before branches")
    if is_home_network:
        # If user is in home network, show friendly apps
        print("homenet")
        for app_type in allowed_app_types:
            if app_type.name == "Restore" and is_cracked:
                applicable_app_types.append(app_type.id)
            elif app_type.name == "Firewall":
                applicable_app_types.append(app_type.id)
            elif app_type.name == "Sweep" and node.order == len(network.nodes.all()) - 1:  # and any(app.name == "Trojan" for app in node.apps):
                print("deepest node reached, homenet")
                applicable_app_types.append(app_type.id)
            elif app_type.name in ["Tracer"]:
                print("traceradded for home user")
                applicable_app_types.append(app_type.id)
    else:
        # If user is not in home network, show hostile and general apps
        print("hostile")
        for app_type in allowed_app_types:
            if app_type.name in ["Backdoor", "Sword", "Banhammer", "Zap", "Shield", "Cloak", "Tracer"]:
                applicable_app_types.append(app_type.id)
            elif app_type.name in ["Siphon", "Crawler"] and not is_cracked:
                # print("siphonadded")
                applicable_app_types.append(app_type.id)
            elif app_type.name == "Trojan" and node.order == len(network.nodes.all()) - 1 and (is_cracked or node_type.name in ["Blank", "Area"]):
                print("deepest node reached, intruder")
                # Make Trojan app available under specific conditions
                applicable_app_types.append(app_type.id)
    # print("get_applicable_inventory_apps ifbranch ended")
    # Count each applicable AppType in the user's inventory that has not been used yet (use_timestamp is None)
    inventory_counts = Inventory.query.join(
        App, Inventory.app_id == App.id
    ).filter(
        Inventory.user_id == user_id, App.use_timestamp.is_(None)
    ).with_entities(
        App.app_type_id, func.count(App.app_type_id)
    ).group_by(
        App.app_type_id
    ).all()

    # Fetch details of each AppType
    app_types = AppType.query.filter(AppType.id.in_([item[0] for item in inventory_counts])).all()

    # Prepare data for the template
    user_apps = []
    for app_type_id, count in inventory_counts:
        app_type = AppType.query.get(app_type_id)
        is_applicable = app_type_id in applicable_app_types
        user_apps.append({'app_type': app_type.name, 'count': count, 'applicable': is_applicable})
        
    return user_apps


def get_node_type_by_id(node_id):
    """Query the database for the type of any given node using its ID."""
    # Fetch the node with the given ID
    node = Node.query.get(node_id)
    print("node_id: ", node_id)
    print("node: ", node)
    # Check if the node exists
    if not node:
        raise ValueError(f"No node found with ID {node_id}")

    # Return the name of the node's type
    return node.node_type.name


def node_user_management(user_id, old_node_id=None, new_node_id=None):
    # who_called_me("node_user_management")
    print("node_user_management called")
    """
    Manage node - user interactions.
    Manage the node_users and met_users tables when a netrunner navigates between nodes or exits the network.

    :param user_id: ID of the netrunner.
    :param current_node_id: ID of the node the netrunner is currently in. None if the netrunner is entering a network.
    :param new_node_id: ID of the node the netrunner is moving to. None if the netrunner is exiting the network.
    :param exit_network_node: Boolean indicating if the netrunner is exiting the network.
    """

    # Check if the user just entered the network or refreshed the node page
    if old_node_id == new_node_id:
        print("User refreshed the node page.")
        # Additional logic for when the user refreshes the node page
    if old_node_id is None:
        print("User entered the network.")
        # Additional logic for when the user enters the network 


    # Check if the user moved from one node to another
    elif old_node_id is not None and new_node_id is not None and old_node_id != new_node_id:
        print(f"User moved from node {old_node_id} to node {new_node_id}.")
        node_left = Node.query.get(old_node_id)  # this is the node object where user just left
        print("node_left: ", node_left)
        # Additional logic for handling the node the user just left

    node_entered = Node.query.get(new_node_id)  # this is the node object where user just entered

    # current_node = Node.query.join(NodeUsers, Node.id == NodeUsers.node_id).filter(NodeUsers.user_id == user_id).first()
    old_node = None
    if old_node_id is not None:
        old_node = Node.query.get(old_node_id)
    if old_node is not None:
        print("** ** ** ** ** ** ** ** current_node.node_type.name and id, by direct query: ", old_node.node_type.name, old_node.id)

    print("** ** ** ** ** ** ** ** node_entered.node_type.name and id, by direct query: ", node_entered.node_type.name, node_entered.id)
    print("node_user_management was called with current_node_id: ", old_node_id)
    print("node_user_management was called with new_node_id: ", new_node_id)

    # Check if a specific node_id was provided in the request
    node_id = request.args.get('node_id')
    if node_id is not None:
        # Query for the specified node
        node = Node.query.get(node_id)
        print("node_user_management function, node by query at the beginning of if node_id is not None branch: ", node)
        # Manage the node_users table for navigation
        if old_node:
            print("node_user_management function, current node at the end of if node_id is not None branch: ", old_node)
    else:
        # If no node_id was provided, continue to return the first node
        node = node_entered
        if node and node.order == 0:
            print("node_user_management function, no node_id was provided, node = current_node: ", node)

    # data collection to pass to the combat.check_interaction function:
    if node:
        print("all good we have node info: ", node)  # all good we have node info
        print(" ")
    else:
        print("no node info so we are in the first node")
        # current_qrcode = session.get('current_qrcode')
        # network_id = current_qrcode.split('-')[-1]

    # Innentől szétpakolni új funkciókba, amelyek korrekt session datát használnak.
    # ********************************************************************************
        
    user_org_relations = UserOrganization.query.filter_by(user_organization_id=user_id).all()
    netrunner_organizations = [relation.organization_id for relation in user_org_relations]
    network = Network.query.get(node_entered.network_id)
    network_organization = network.organization_id
    node_position = node.order
    node_type = NodeType.query.get(node.node_type_id)
    
    # Check if an entry for the user already exists in any node
    user_entry = NodeUsers.query.filter_by(user_id=user_id).first()

    # If the user already has an entry, update it with the new node id
    if user_entry:
        print("nodeuser entry exists, updating")
        user_entry.node_id = new_node_id
        if old_node:
            user_entry.interaction_data = None
            user_entry.attack_data = None
    else:
        # If the user doesn't have an entry, create one for the new node
        print("nodeUsers entry does not exist, creating")
        new_node_user = NodeUsers(user_id=user_id, node_id=new_node_id)
        db.session.add(new_node_user)
    db.session.commit()

    # This is to trigger the White IC actions, if the WIC node is not cracked and cloak used / not used.
    if old_node and hasattr(old_node, 'node_type'):
        print("Standard node navigation path, collecting data")
        print("exited node type", old_node.node_type.name)
        
        old_node_position = old_node.order

        if old_node_position < node_position and old_node.node_type.name == "White IC":
            # print("White IC path")
            whiteic_active = node_status_check_whiteic(old_node_id, user_id)
            # print("whiteic_active: ", whiteic_active)
            if whiteic_active:
                # print("this call should be executed when the user leaves a white IC node AND not used Cloak")
                # this call should be executed when the user leaves a white IC node AND not used Cloak
                result = {"message": "Traced by White IC!"}
                white_ic_alert(user_id ,old_node.network_id)
                print(result)

    
    result = check_interaction(
        node_id=node.id,
        node_type_name=node_type.name,
        app_id=None,
        app_type_name=None,
        app_type_enum=None,
        is_cracked=node.is_cracked,
        network_organization=network_organization,
        netrunner_organizations=netrunner_organizations,
        network_length=len(network.nodes.all()),
        node_position=node.order,
        attacker_id=user_id,
        user_id=user_id,
        second_app_id=None,
        second_app_type_name=None
    )
    print("result: ", result)

    # If the user is entering a new node
    if new_node_id:
        print("node_user_management function, new_node_id branch, user is entering a new node: ", new_node_id)
        new_node = Node.query.get(new_node_id)
        network_id = new_node.network_id

        # Update the location of the moving user in the records of all users he has previously met
        met_users_of_current = MetUsers.query.filter_by(met_user_id=user_id).all()
        for met_user in met_users_of_current:
            met_user.current_order = new_node.order
            met_user.current_node_name = new_node.name
        db.session.commit()

        # Fetch the newly entered user's data
       
        # Get all users present in the new node
        users_in_node = NodeUsers.query.filter_by(node_id = new_node_id).all()
        # Notify other users in the same node of the new user entry
        print("see who is in node", new_node_id)
        for user_entry in users_in_node:
            print("user in same node:", user_entry.user_id)
            if user_entry.user_id != user_id:  # Don't notify the user who just entered
                sse_push(user_entry.user_id, 'user_entered_node', {'id': user_id})

                # For each user in the new node, create MetUser entry if missing
                met_user_entry = MetUsers.query.filter_by(network_id=network_id, user_id=user_id, met_user_id=user_entry.user_id).first()
                if not met_user_entry:
                    met_user_entry = MetUsers(network_id=network_id, user_id=user_id, met_user_id=user_entry.user_id, tracer_used=False, current_order=new_node.order, current_node_name=new_node.name)
                    db.session.add(met_user_entry)

                other_met_user_entry = MetUsers.query.filter_by(network_id=network_id, user_id=user_entry.user_id, met_user_id=user_id).first()
                if not other_met_user_entry:
                    other_met_user_entry = MetUsers(network_id=network_id, user_id=user_entry.user_id, met_user_id=user_id, tracer_used=False, current_order=new_node.order, current_node_name=new_node.name)
                    db.session.add(other_met_user_entry)

        if old_node is not None:
            users_in_old_node = NodeUsers.query.filter_by(node_id = old_node_id).all()
            # Notify other users in the same node of the new user entry
            for user_entry in users_in_old_node:
                if user_entry.user_id != user_id:  # Don't notify the user who just entered
                    sse_push(user_entry.user_id, 'leave_node', {'id': user_id})

        # Commit the changes to the database
        db.session.commit()
        # Fetch the network ID of the new node
        network_id = new_node.network_id
        update_met_users(network_id)
        


def node_status_check_whiteic(node_id, user_id):
    # Check if the node is cloaked for this user
    cloak_data = session.get("cloak_data", {})
    user_cloak_data = cloak_data.get(str(user_id), {})
    if user_cloak_data.get("node_id") == node_id:
        elapsed_time = datetime.now(timezone.utc) - datetime.fromisoformat(user_cloak_data["timestamp"])
        remaining_time = timedelta(minutes=5) - elapsed_time
        if remaining_time > dt.timedelta():
            # Notify the user of the remaining cloak time and the message
            minutes, seconds = divmod(remaining_time.seconds, 60)
            if "message" in user_cloak_data:
                message = user_cloak_data["message"]
            else:
                message = "Üzenet összeállítási hiba a node_status_check_whiteic funkcióban."
            session["server_messages"] = f"{message} - {minutes}:{seconds}"
            return False  # White IC is active
    return True  # White IC actions still cloaked


def use_tracer(user_id, node_id):
    print("use_tracer called, started by user: ", user_id)
    current_node = Node.query.get(node_id)

    userRecord = NodeUsers.query.filter(NodeUsers.user_id==user_id).first()
    # Broadcast the Tracer app usage to all users in the same network except the one using the Tracer
    users_in_network = NodeUsers.query.filter(NodeUsers.node_id==node_id, NodeUsers.user_id!=user_id).all()
    print("users_in_network: ", users_in_network)

    if len(users_in_network) == 0:
        #only you are in this node
        return jsonify({"status": "no_target", "message": "No users in this Node to Trace!"})

    # Get the app type ID for cloak and tracer
    cloak_app_type_id = AppType.query.filter_by(name='Cloak').first().id
    tracer_app_type_id = AppType.query.filter_by(name='Tracer').first().id
    print("cloak_app_type_id: ", cloak_app_type_id)
    print("tracer_app_type_id: ", tracer_app_type_id)

    # Update current user's first unused Tracer app in their inventory with a timestamp
    user_tracer_app = Inventory.query.join(App).filter(Inventory.user_id == user_id, App.app_type_id == tracer_app_type_id, App.use_timestamp.is_(None)).first()
    print("user_tracer_app: ", user_tracer_app)
    if user_tracer_app:
        user_tracer_app.app.use_timestamp = datetime.now()
        print("tracer app used up.")
        db.session.commit()
    else:
        print("no tracer app in inventory")
        return jsonify({"status": "no_tracer_available", "message": "No Tracer in inventory!"})

    trace_ids = []

    for user_entry in users_in_network:
        if user_entry.user_id != user_id:
            print("user_entry.user_id: ", user_entry.user_id)
            # Check if the user has a cloak app in their inventory
            cloak_app_inventory = Inventory.query.join(App).filter(Inventory.user_id == user_entry.user_id, App.app_type_id == cloak_app_type_id, App.use_timestamp.is_(None)).first()
            print("cloak_app_inventory: ", cloak_app_inventory)
            if cloak_app_inventory:
                print("target has cloak, sse notif for pvp attack sent")
                sse_push(user_entry.user_id, "pvp_attack", {"app":"Tracer", "attacker":user_id})
                trace_ids.append(user_entry.user_id)
            else:
                # attack hits automatically
                pvp_app_hit("Tracer", node_id, user_entry.user_id, user_id)

    if len(trace_ids) > 0:
        userRecord.attack_data = {"app":"Tracer", "time":datetime.utcnow().isoformat(), "target":trace_ids}


    db.session.commit()
    return jsonify({"status": "success", "message": "Tracer app used successfully"})


@netrunning_blueprint.route('/trigger_app_deletion', methods=['POST'])
def trigger_app_deletion():
    data = request.json
    user_id = data.get('user_id')
    result = delete_random_app(user_id)
    # Check if the message is present in the result
    message = result.get('target_message', 'No app was deleted!')

    return {"message": message}


@netrunning_blueprint.route('/fetch_file_list/<int:node_id>', methods=['GET'])
def fetch_file_list(node_id):
    # print("fetch_file_list called, node: ", node_id)
    # Fetch the Node based on node_id
    node = Node.query.get(node_id)

    # Check if the node is of type Intel
    if node.node_type.name != "Intel":
        return jsonify({"error": "Not an Intel node"})
    # print("node is intel")
    # Fetch the Files based on the file_ids in the Node
    files = File.query.filter(File.id.in_(node.file_ids)).all()
    # print("files: ", files)
    # Return the file names as a JSON response
    return jsonify({"file_names": [file.name for file in files]})


# Back calls from frontend Jinja2, debug purposes
def debug_print(value):
    print(value)
    return value  # Ensure the filter doesn't alter the value it's applied to

# Using apps in inventory
@netrunning_blueprint.route('/use_app/attack', methods=['POST'])
def use_app_pvp():
    print("received a netrunning attack:", request)
    userId = session['user_id']
    nodeId = int(request.json.get('node'))
    targetId = int(request.json.get('target'))
    appTypeName = request.json.get('appTypeName')
    #get nodeuser records
    userRecord = NodeUsers.query.filter_by(node_id = nodeId, user_id = userId).first()
    targetRecord = NodeUsers.query.filter_by(node_id = nodeId, user_id = targetId).first()
    #if target is not in same node, fail state
    if targetRecord is None:
        return jsonify({"error":"target_not_in_node"}), 400
    if userRecord is None:
        return jsonify({"error":"user_not_in_node"}), 400
    #if an attack is already pending from user, fail state
    if userRecord.attack_data is not None:
        return jsonify({"error":"attack_already_running"}), 400
    #get app
    # Fetch the app type
    app_type = AppType.query.filter_by(name=appTypeName).first()
    if app_type is None:
        print ("MAJOR FUCKUP - app type not in db:", app_type)
        return jsonify({"error": "app_type_not_in_db"})

    # Fetch the first UNUSED app of the specified type from the user's inventory
    inventory_app = Inventory.query.join(App, Inventory.app_id == App.id).filter(
        Inventory.user_id == userId, App.app_type_id == app_type.id, App.use_timestamp.is_(None)
    ).first()
    if inventory_app is None or inventory_app.app is None:
        return jsonify({"error":"app_not_in_inventory"})
    
    app = inventory_app.app

    #check app type
    if app.app_type.name not in ["Banhammer","Sword", "Zap"]:
        return jsonify({"error":"app_not_applicable"}), 400

    #check if defender even has applicable defense apps
    defenseAppType = AppType.query.filter_by(name="shield").first()
    if defenseAppType is None:
        print("MAJOR FUCKUP, defense app type is not in db!")
        return jsonify({"error":"app_type_not_in_db"}), 500
    
    # app is used
    app.use_timestamp = datetime.utcnow()
    db.session.commit()

    defense_app = Inventory.query.join(
        App, Inventory.app_id == App.id
    ).filter(
        Inventory.user_id == targetId, App.use_timestamp.is_(None), App.app_type_id == defenseAppType.id  # We are only interested in the defense app
    ).first()
    print("defense app is", defense_app)

    # if target has no defense apps, hit is successful
    if defense_app is None:
        print("defender has no applicable defense apps")
        pvp_app_hit(app.app_type.name, nodeId, targetId, userId)
        return jsonify({"result":"success"}), 200

    #send sse for the attack prompt
    sse_push(targetId, "pvp_attack", {"app":app.app_type.name, "attacker":userId})
    #create attack record
    userRecord.attack_data = {"app":app.app_type.name, "time":datetime.utcnow().isoformat(), "target":targetId}
    db.session.commit()
    
    return jsonify({"result":"pending"}), 200

# Using apps in inventory
@netrunning_blueprint.route('/use_app/respond', methods=['POST'])
def respond_to_pvp():
    userId = session['user_id']
    nodeId = int(request.json.get('node'))
    attackerId = int(request.json.get('attacker'))
    responseText = request.json.get('response')
    attackRecord = NodeUsers.query.with_for_update(of=NodeUsers).filter_by(node_id = nodeId, user_id = attackerId).first()
    if attackRecord is None or attackRecord.attack_data is None:
        #attack was cancelled becase e.g. attacker left the node
        return jsonify({"error":"attack_already_cancelled"}), 200

    appTypeName = attackRecord.attack_data.get("app")
    targetId = attackRecord.attack_data.get("target")
    if appTypeName not in ["Banhammer","Sword", "Tracer", "Zap"]:
        print("apptype name in attack records looks invalid:", attackRecord.attack_data)
        return jsonify({"error":"attack_type_invalid"}), 200
    if hasattr(targetId, '__len__') and (not isinstance(targetId, str)):
        targetId.remove(userId)
        if len(targetId) == 0:
            attackRecord.attack_data = None
        else:
            attackRecord.attack_data["target"] = targetId
            flag_modified(NodeUsers, "attack_data")
    else:
        attackRecord.attack_data = None
    db.session.commit()

    if responseText == 'yes':
        print("positive response from ", userId)
        if appTypeName == "Trace":
            defenseAppType = AppType.query.filter_by(name="Cloak").first()
        else:
            defenseAppType = AppType.query.filter_by(name="Shield").first()
        if defenseAppType is None:
            print("MAJOR FUCKUP, defense app type is not in db!")
            return jsonify({"error":"app_type_not_in_db"}), 200
        defense_app_inventory = Inventory.query.join(
            App, Inventory.app_id == App.id
            ).filter(
                Inventory.user_id == userId
            ).filter(
                App.use_timestamp.is_(None)  # This is to filter already used apps
            ).filter(
                App.app_type_id == defenseAppType.id  # We are only interested in the defense app
            ).first()

        # if target has no defense apps, hit is successful
        if defense_app_inventory is None:
            print("whoops, no more defense apps")
            pvp_app_hit(appTypeName, nodeId, userId, attackerId)
            return jsonify({"message":"no_defense_apps"}), 200

        defense_app_inventory.app.use_timestamp = datetime.now()
        db.session.commit()
        sse_push(attackerId, "pvp_result", {"app":appTypeName, "target":userId, "success":0})

        return jsonify({"result":"success"}), 200
    elif responseText == 'no':
        pvp_app_hit(appTypeName, nodeId, userId, attackerId)
        print("negative response from ", userId)
        return jsonify({"result":"hit"}), 200
    else:
        print("invalid response from ", userId)
    return jsonify({"error":"unhandled_route"}), 200


        