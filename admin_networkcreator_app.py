from flask import Blueprint, request, jsonify
from database import db, Network, Node, NodeType, File
from flask import current_app


# Create a new blueprint
network_creator = Blueprint('network_creator', __name__, url_prefix='/admin')

@network_creator.route('/get_node_types', methods=['GET'])
def get_node_types():
    with current_app.app_context():
        try:
            # Get all NodeTypes from the database
            node_types = NodeType.query.all()

            # Transform the NodeType objects into dictionaries to make them serializable
            node_types_dict = [{'id': node_type.id, 'name': node_type.name} for node_type in node_types]

            # Return the serialized list of NodeTypes
        except Exception as e:
            raise e
        return jsonify(node_types_dict)


@network_creator.route('/create_network', methods=['POST'])
def create_network():
    with current_app.app_context():
        if request.is_json:
            data = request.get_json()
        else:
            return "Unsupported Media Type", 415

        network_length = int(data.get('length', 0))

        new_network = Network(
            name=data['name'],
            organization_id=data['organization_id']
        )
        db.session.add(new_network)
        db.session.commit()  # Need to commit to get an ID for the network

        for i in range(network_length):
            new_node = Node(
                network_id=new_network.id,
                name=data['nodes'][i]['name'],
                order=i,
                node_type_id=data['nodes'][i]['node_type_id'],
                max_users=data['nodes'][i].get('max_users', 2),  # default value if not provided
                is_cracked=False,  # Setting default value for new node
                file_ids=data['nodes'][i].get('file_ids', []),

            )
            print(f"New Node before add: {vars(new_node)}")  # Printing new node details
            db.session.add(new_node)

        db.session.commit()

        return {'status': 'success'}, 201


@network_creator.route('/get_files', methods=['GET'])
def get_files():
    with current_app.app_context():
        try:
            # Get all Files from the database where original_owner_id and copied_by_id are both None
            files = File.query.filter(File.original_owner_id.is_(None), File.copied_by_id.is_(None)).all()
            # Transform the File objects into dictionaries to make them serializable
            files_dict = [{'id': file.id, 'name': file.name} for file in files]
            # Return the serialized list of Files
            return jsonify(files_dict)
        except Exception as e:
            raise e

