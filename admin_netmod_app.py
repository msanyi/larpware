from flask import Blueprint, request, jsonify, render_template
from database import Network, NodeType, File, Node, Organizations, User, Digitalmarketlisting, NodeUsers, NodeOperationsHistory
from sqlalchemy.exc import SQLAlchemyError
from database import db

admin_netmod_app = Blueprint('admin_netmod_app', __name__, url_prefix='/admin')


@admin_netmod_app.route('/get_networks', methods=['GET'])
def get_networks():
    networks = Network.query.all()
    return jsonify([network.serialize() for network in networks])


@admin_netmod_app.route('/get_network/<int:network_id>', methods=['GET'])
def get_network(network_id):
    network = Network.query.get(network_id)
    return jsonify(network.serialize())


@admin_netmod_app.route('/get_node_types', methods=['GET'])
def get_node_types():
    node_types = NodeType.query.all()
    return jsonify([node_type.serialize() for node_type in node_types])


@admin_netmod_app.route('/get_files', methods=['GET'])
def get_files():
    # Get all Files from the database where original_owner_id and copied_by_id are both None
    files = File.query.filter(File.original_owner_id.is_(None), File.copied_by_id.is_(None)).all()
    return jsonify([file.serialize() for file in files])


@admin_netmod_app.route('/update_network', methods=['POST'])
def update_network():
    print("update network called")
    data = request.get_json()
    print("data: ", data)

    # Error handling for missing data
    if not all(key in data for key in ['id', 'name', 'organization_id', 'nodes']):
        print("Missing necessary data")  # Debugging line
        return jsonify({'message': 'Missing necessary data'}), 400
    print("all data OK")
    # Get the network
    network = Network.query.get(data['id'])
    if not network:
        print("Network not found")
        return jsonify({'message': 'Network not found'}), 404
    print("network OK")
    # Step 1: Find the Watchdog User ID
    organization_id = network.organization_id
    org = Organizations.query.get(organization_id)
    print("file ownership part, organization_id:", organization_id)
    print("file ownership part, user_organizations:", org)
    watchdog_user_id = None

    watchdog_username = f"{org.orgname} Architecture Watchdog"
    watchdog = User.query.filter_by(username=watchdog_username).first()
 
    if watchdog is None:
        return jsonify({'message': 'Architecture Watchdog user not found for the organization'}), 400
    
    watchdog_user_id=watchdog.id
    print("file ownership part, watchdog_user_id:", watchdog_user_id)
    # Step 2: Update File's original_owner_id and Step 3: Remove the File ID from Digitalmarketlisting
    for node_data in data['nodes']:
        file_ids = node_data['file_ids']
        print("file ownership part, file_ids:", file_ids)
        files = File.query.filter(File.id.in_(file_ids)).all()
        for file in files:
            file.original_owner_id = watchdog_user_id
        Digitalmarketlisting.query.filter(Digitalmarketlisting.file_id.in_(file_ids)).delete(synchronize_session='fetch')

    # Commit the changes
    db.session.commit()

    # Update network details
    network.name = data['name']
    network.organization_id = data['organization_id']

    # Get IDs of nodes to be deleted
    node_ids_to_delete = [node.id for node in network.nodes]

    # Delete old nodes
    if node_ids_to_delete:
        NodeUsers.query.filter(NodeUsers.node_id.in_(node_ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()
        NodeOperationsHistory.query.filter(NodeOperationsHistory.node_id.in_(node_ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()
        Node.query.filter(Node.id.in_(node_ids_to_delete)).delete(synchronize_session=False)
        db.session.commit()

    # Add new nodes
    try:
        for node_data in data['nodes']:
            node = Node(
                network_id=network.id,
                name=node_data['name'],
                order=node_data['order'],
                is_cracked=node_data.get('is_cracked', False),
                file_ids=node_data['file_ids'],
                node_type_id=node_data['node_type_id'],
                max_users=node_data.get('max_users', 2)
            )
            db.session.add(node)
        db.session.commit()
    except SQLAlchemyError as e:
        # print("Error updating the network: ", e)  # Debugging line
        db.session.rollback()
        return jsonify({'message': 'There was an error updating the network: ' + str(e)}), 500
    return jsonify(network.serialize()), 200


@admin_netmod_app.route('/network_modifier', methods=['GET'])
def network_modifier():
    print("admin netmod")
    return render_template('admin_networkmodifier.html')
