def user_to_dict(user, include_friends=False):
    user_dict = {
        'id': user.id,
        'username': user.username,
        'balance': user.balance,
        'wound': user.wound,
        'is_netrunner': user.is_netrunner,
        'is_fixer': user.is_fixer,
        'citynet': user.citynet
        # 'inventories': [inventory_to_dict(inventory) for inventory in user.inventories]
    }
    if include_friends:
        user_dict['friends'] = [friendship_to_dict(friendship) for friendship in user.friends]
    return user_dict


def friendship_to_dict(friendship):
    return {
        'user_id': friendship.user_id,
        'friend_id': friendship.friend_id,
        'friend': user_to_dict(friendship.friend)  # This won't include the 'friends' relationship
    }


def user_organization_to_dict(user_organization):
    return {
        'organization_id': user_organization.organization_id
    }


def organization_to_dict(organization):
    return {
        'id': organization.id,
        'orgname': organization.orgname,
        'users': [user_organization_to_dict(user_org) for user_org in organization.users]
    }


def message_to_dict(message):
    return {
        'id': message.id,
        'sender_id': message.sender_id,
        'receiver_id': message.receiver_id,
        'messagecontent': message.messagecontent,
        'timesent': message.timesent.strftime('%Y-%m-%d %H:%M:%S') if message.timesent else None,
        'isread': message.isread.strftime('%Y-%m-%d %H:%M:%S') if message.isread else None,
        'sender': user_to_dict(message.sender),
        'receiver': user_to_dict(message.receiver)
    }


def bulletinboard_to_dict(bulletinboard):
    return {
        'id': bulletinboard.id,
        'boardtype': bulletinboard.boardtype,
        'organization_id': bulletinboard.organization_id
    }


def post_to_dict(post):
    return {
        'id': post.id,
        'board_id': post.board_id,
        'poster_id': post.poster_id,
        'postcontent': post.postcontent,
        'timeposted': post.timeposted.strftime('%Y-%m-%d %H:%M:%S') if post.timeposted else None
    }


def reaction_to_dict(reaction):
    return {
        'id': reaction.id,
        'user_id': reaction.user_id,
        'message_id': reaction.message_id,
        'post_id': reaction.post_id,
        'reaction_type': reaction.reaction_type,
        'created_at': reaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if reaction.created_at else None
    }


def app_type_to_dict(app_type):
    return {
        'id': app_type.id,
        'name': app_type.name,
        'description': app_type.description,
        'is_netrunnersonly': app_type.is_netrunnersonly,
        'type': app_type.type
    }


def app_to_dict(app):
    return {
        'id': app.id,
        'app_type_id': app.app_type_id,
        'name': app.name,
        'use_timestamp': app.use_timestamp.strftime('%Y-%m-%d %H:%M:%S') if app.use_timestamp else None,
        'app_type': app_type_to_dict(app.app_type)
    }


def network_to_dict(network):
    return {
        'id': network.id,
        'name': network.name,
        'organization_id': network.organization_id,
        'nodes': [node_to_dict(node) for node in network.nodes]
    }


def node_to_dict(node):
    return {
        'id': node.id,
        'network_id': node.network_id,
        'name': node.name,
        'order': node.order,
        'is_cracked': node.is_cracked,
        'file_ids': node.file_ids,
        'node_type_id': node.node_type_id,
        'crack_timestamp': node.crack_timestamp.strftime('%Y-%m-%d %H:%M:%S') if node.crack_timestamp else None,
        'max_users': node.max_users,
        'node_type': node_type_to_dict(node.node_type)
    }


def node_type_to_dict(node_type):
    return {
        'id': node_type.id,
        'name': node_type.name,
        'description': node_type.description,
        'interaction': node_type.interaction,
        'seconds_to_solve': node_type.seconds_to_solve,
        'send_message': node_type.send_message,
        'delete_app': node_type.delete_app,
        'changes_wound_status': node_type.changes_wound_status,
        'apps': [app_type_to_dict(app) for app in node_type.apps]
    }


def file_to_dict(file):
    return {
        'id': file.id,
        'name': file.name,
        'content': file.content,
        'original_owner_id': file.original_owner_id,
        'copied_by_id': file.copied_by_id,
        'original_owner': user_to_dict(file.original_owner) if file.original_owner else None,
        'copied_by': user_to_dict(file.copied_by) if file.copied_by else None

    }


def node_operations_history_to_dict(history):
    return {
        'id': history.id,
        'node_id': history.node_id,
        'user_id': history.user_id,
        'operation_type': history.operation_type,
        'timestamp': history.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'app_used': app_to_dict(history.app_used) if history.app_used else None
    }


def node_users_to_dict(node_users):
    return {
        'id': node_users.id,
        'node_id': node_users.node_id,
        'user_id': node_users.user_id
    }


def access_point_to_dict(access_point):
    return {
        'id': access_point.id,
        'qr_code': access_point.qr_code,
        'network_id': access_point.network_id
    }


def inventory_to_dict(inventory):
    return {
        'id': inventory.id,
        'user_id': inventory.user_id,
        'app_id': inventory.app_id,
        'file_id': inventory.file_id,
    }


def qrcode_to_dict(qrcode):
    return {
        'id': qrcode.id,
        'qrcode': qrcode.qrcode,
        'qrcodetype': qrcode.qrcodetype,
        'targetid': qrcode.targetid
    }


def digitalmarketlisting_to_dict(listing):
    if not hasattr(listing, 'id'):
        return {}
    serialized_listing = {
        'id': listing.id,
        'name': listing.name,
        'description': listing.description,
        'price': listing.price,
        'listing_type': listing.listing_type,
        'app_id': listing.app_id,
        'file_id': listing.file_id,
        'market_type': listing.market_type
    }

    # If the listing has an associated app or file, add their serialized form to the dictionary
    if listing.app:
        serialized_listing['app'] = app_to_dict(listing.app)
    if listing.file:
        serialized_listing['file'] = file_to_dict(listing.file)

    return serialized_listing
