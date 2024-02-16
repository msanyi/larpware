from flask import Blueprint, jsonify, render_template, session, request
from database import User, Bulletinboards, Boardview, Posts, UserOrganization, db, Reaction, File
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from navbar import NavBarInfo

boards_app = Blueprint('boards_app', __name__)

@boards_app.route('/api/boards/<int:board_id>/posts', methods=['GET'])
def get_board_posts(board_id):
    print("get_board_posts called")
    user_id = session.get('user_id')
    seen_post_ids = [reaction.post_id for reaction in Reaction.query.filter_by(user_id=user_id, reaction_type='seen').all()]
    posts = Posts.query.filter_by(board_id=board_id).order_by(Posts.timeposted.desc()).limit(20)

    # Getting user reactions
    user_reactions = Reaction.query.filter_by(user_id=user_id).all()
    user_reactions_map = {reaction.post_id: reaction.reaction_type for reaction in user_reactions}

    post_data = [{
        'id': post.id,
        'content': post.postcontent,
        'user': User.query.filter_by(id=post.poster_id).first().username,
        'file': {
            'id': post.file.id,
            'name': post.file.name,
            'content': post.file.content,
            'original_owner': {
                'id': post.file.original_owner.id,
                'username': post.file.original_owner.username,
                'citynet': post.file.original_owner.citynet
            } if post.file.original_owner else None,
            'copied_by': {
                'id': post.file.copied_by.id,
                'username': post.file.copied_by.username,
                'citynet': post.file.copied_by.citynet
            } if post.file.copied_by else None,
        } if post.file else None,
        'seen_count': Reaction.query.filter_by(post_id=post.id, reaction_type='seen').count(),
        'like_count': Reaction.query.filter_by(post_id=post.id, reaction_type='like').count(),
        'dislike_count': Reaction.query.filter_by(post_id=post.id, reaction_type='dislike').count(),
        'user_reaction': user_reactions_map.get(post.id),
        'user_reacted': Reaction.query.filter_by(post_id=post.id, user_id=user_id).filter(Reaction.reaction_type != 'seen').first() is not None,
        'user_has_seen': Reaction.query.filter_by(post_id=post.id, user_id=user_id, reaction_type='seen').first() is not None,
        'posted_at': (post.timeposted + timedelta(hours=2)).strftime("%d/%m %H:%M")
    } for post in posts]
    # print("Posts content: ", post_data)
    return jsonify({'posts': post_data})

@boards_app.route('/boards/<int:board_id>', methods=['GET'])
def get_board(board_id):
    args = request.args
    page = args.get("page", default=1, type=int)
    print("get_board_posts called")
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    board_name = Bulletinboards.query.get(board_id).name
    accessible_boards = []

    # Everyone can access the public board
    public_board = Bulletinboards.query.filter_by(boardtype='public').first()
    if public_board:
        accessible_boards.append(public_board.id)

    # Check if user is a netrunner
    if user.is_netrunner:
        darkweb_board = Bulletinboards.query.filter_by(boardtype='darkweb').first()
        if darkweb_board:
            accessible_boards.append(darkweb_board.id)

    # Check if user is part of an organization and fetch the associated secure board
    user_orgs = UserOrganization.query.filter_by(user_organization_id=user_id).all()
    for user_org in user_orgs:
        if user_org.endtime is None or user_org.endtime > datetime.utcnow():
            org_board = Bulletinboards.query.filter_by(boardtype='secure', organization_id=user_org.organization_id).first()
            if org_board:
                accessible_boards.append(org_board.id)

    if board_id not in accessible_boards:
        return jsonify({"error":"Permission denied"}), 403

    posts = Posts.query.filter_by(board_id=board_id).order_by(Posts.timeposted.desc()).paginate(page=page, per_page=10)

    paginationObject = {
        'page':posts.page,
        'total':posts.pages,
        'prev_num': posts.prev_num,
        'next_num': posts.next_num,
        'has_next': posts.has_next,
        'has_prev': posts.has_prev
    }
    # Getting user reactions
    user_reactions = Reaction.query.filter_by(user_id=user_id).all()
    user_reactions_map = {reaction.post_id: reaction.reaction_type for reaction in user_reactions}

    post_data = [{
        'id': post.id,
        'content': post.postcontent,
        'user': User.query.filter_by(id=post.poster_id).first().username,
        'file': {
            'id': post.file.id,
            'name': post.file.name,
            'content': post.file.content,
            'original_owner': {
                'id': post.file.original_owner.id,
                'username': post.file.original_owner.username,
                'citynet': post.file.original_owner.citynet
            } if post.file.original_owner else None,
            'copied_by': {
                'id': post.file.copied_by.id,
                'username': post.file.copied_by.username,
                'citynet': post.file.copied_by.citynet
            } if post.file.copied_by else None,
        } if post.file else None,
        'seen_count': Reaction.query.filter_by(post_id=post.id, reaction_type='seen').count(),
        'like_count': Reaction.query.filter_by(post_id=post.id, reaction_type='like').count(),
        'dislike_count': Reaction.query.filter_by(post_id=post.id, reaction_type='dislike').count(),
        'user_reaction': user_reactions_map.get(post.id),
        'user_reacted': Reaction.query.filter_by(post_id=post.id, user_id=user_id).filter(Reaction.reaction_type != 'seen').first() is not None,
        'user_has_seen': Reaction.query.filter_by(post_id=post.id, user_id=user_id, reaction_type='seen').first() is not None,
        'posted_at': (post.timeposted + timedelta(hours=2)).strftime("%d/%m %H:%M")
    } for post in posts.items]
    print(post_data)
    # print("Posts content: ", post_data)
    return render_template('board_view.html', user_id=user_id, board_id=board_id, board_name=board_name, posts=post_data, pages=paginationObject, headerinfo=NavBarInfo())

@boards_app.route('/api/boards/post', methods=['POST'])
def post_to_board():
    print("Entering post_to_board function")
    user_id = session.get('user_id')
    post_content = request.form.get('content')
    board_id = request.form.get('board_id')
    file_id = request.form.get('file_id')  # Get file_id from the request

    print(f"user_id: {user_id}, post_content: {post_content}, board_id: {board_id}, file_id: {file_id}")

    if not user_id:
        print("User not logged in or session expired")
        return jsonify({'success': False, 'message': 'User not logged in or session expired'}), 400
    if not post_content and not file_id:
        print("Both post content and file_id are missing")
        return jsonify({'success': False, 'message': 'Post content and file_id are both missing'}), 400
    if not board_id:
        print("Board ID is missing")
        return jsonify({'success': False, 'message': 'Board ID is missing'}), 400

    new_post = Posts(board_id=board_id, poster_id=user_id, postcontent=post_content)
    if file_id:
        # Validate the file_id and associate it with the post
        file = File.query.get(file_id)
        if file:
            new_post.file_id = file_id
        else:
            return jsonify({'success': False, 'message': 'File not found'}), 400

    db.session.add(new_post)
    db.session.commit() # commit to make it have an id
    #immediately mark it as seeon so you wont mess up notifications with your own posts
    seen_reaction = Reaction(
            user_id=user_id,
            post_id=new_post.id,
            reaction_type='seen'
        )
    db.session.add(seen_reaction)
    db.session.commit()
    print("Post added successfully")
    return jsonify({'success': True, 'message': "Post added successfully."})

@boards_app.route('/boards', methods=['GET'])
def boards_page():
    user_id = session.get('user_id')
    print("user_id: ", user_id)

    user = User.query.get(user_id)
    accessible_boards = []
    seen_post_ids = [reaction.post_id for reaction in Reaction.query.filter_by(user_id=user_id, reaction_type='seen').all()]

    # Everyone can access the public board
    public_board = Bulletinboards.query.filter_by(boardtype='public').first()
    if public_board:
        accessible_boards.append(public_board)

    # Check if user is a netrunner
    if user.is_netrunner:
        darkweb_board = Bulletinboards.query.filter_by(boardtype='darkweb').first()
        if darkweb_board:
            accessible_boards.append(darkweb_board)

    # Check if user is part of an organization and fetch the associated secure board
    user_orgs = UserOrganization.query.filter_by(user_organization_id=user_id).all()
    for user_org in user_orgs:
        if user_org.endtime is None or user_org.endtime > datetime.utcnow():
            org_board = Bulletinboards.query.filter_by(boardtype='secure', organization_id=user_org.organization_id).first()
            if org_board:
                accessible_boards.append(org_board)

    boards_data = []

    for board in accessible_boards:
        last_viewed = Boardview.query.filter_by(user_id=user_id, board_id=board.id).first()
        if last_viewed:
            new_messages_count = Posts.query.filter(Posts.board_id == board.id, Posts.timestamp > last_viewed.last_viewed_timestamp, Posts.id.notin_(seen_post_ids)).count()

        else:
            new_messages_count = Posts.query.filter_by(board_id=board.id).filter(Posts.id.notin_(seen_post_ids)).count()

        boards_data.append({
            'id': board.id,
            'name': board.name,
            'new_messages_count': new_messages_count
        })

    return render_template('boards_list.html', user_id=user_id, boards=boards_data, headerinfo=NavBarInfo())


@boards_app.route('/api/boards', methods=['GET'])
def list_boards():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    accessible_boards = []
    seen_post_ids = [reaction.post_id for reaction in Reaction.query.filter_by(user_id=user_id, reaction_type='seen').all()]

    # Everyone can access the public board
    public_board = Bulletinboards.query.filter_by(boardtype='public').first()
    if public_board:
        accessible_boards.append(public_board)

    # Check if user is a member of the "Entertec Network"
    # is_member_of_entertec = UserOrganization.query.filter_by(user_organization_id=user_id, organization_id=1).first()
    # if is_member_of_entertec:
    #     newsfeed_board = Bulletinboards.query.filter_by(boardtype='newsfeed').first()
    #    if newsfeed_board:
    #        accessible_boards.append(newsfeed_board)

    # Check if user is a netrunner
    if user.is_netrunner:
        darkweb_board = Bulletinboards.query.filter_by(boardtype='darkweb').first()
        if darkweb_board:
            accessible_boards.append(darkweb_board)

    # Check if user is part of an organization and fetch the associated secure board
    user_orgs = UserOrganization.query.filter_by(user_organization_id=user_id).all()
    for user_org in user_orgs:
        if user_org.endtime is None or user_org.endtime > datetime.utcnow():
            org_board = Bulletinboards.query.filter_by(boardtype='secure', organization_id=user_org.organization_id).first()
            if org_board:
                accessible_boards.append(org_board)

    boards_data = []

    for board in accessible_boards:
        last_viewed = Boardview.query.filter_by(user_id=user_id, board_id=board.id).first()
        if last_viewed:
            new_messages_count = Posts.query.filter(Posts.board_id == board.id, Posts.timestamp > last_viewed.last_viewed_timestamp, Posts.id.notin_(seen_post_ids)).count()

        else:
            new_messages_count = Posts.query.filter_by(board_id=board.id).filter(Posts.id.notin_(seen_post_ids)).count()

        boards_data.append({
            'id': board.id,
            'name': board.name,
            'new_messages_count': new_messages_count
        })

    return jsonify({'boards': boards_data})


@boards_app.route('/api/posts/<int:post_id>/reaction', methods=['POST'])
def handle_post_reaction(post_id):
    user_id = session.get('user_id')
    if not request.json:
        return jsonify({'success': False, 'message': 'Invalid or missing JSON payload.'})
    reaction_type = request.json.get('type')

    try:
        reaction = Reaction(
            user_id=user_id,
            post_id=post_id,
            reaction_type=reaction_type
        )
        db.session.add(reaction)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Reaction added successfully!'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'You have already reacted to this post.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to add reaction due to {str(e)}.'})


@boards_app.route('/api/posts/<int:post_id>/mark-seen', methods=['POST'])
def mark_post_as_seen(post_id):
    user_id = session.get('user_id')

    # Check if already marked as seen
    existing_seen = Reaction.query.filter_by(post_id=post_id, user_id=user_id, reaction_type='seen').first()
    if not existing_seen:
        seen_reaction = Reaction(
            user_id=user_id,
            post_id=post_id,
            reaction_type='seen'
        )
        db.session.add(seen_reaction)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Post marked as seen.'})
    else:
        return jsonify({'success': False, 'message': 'Post already seen.'})

    

