from flask import session
from database import User, Messages, Reaction, Bulletinboards, UserOrganization, Boardview, Posts
from datetime import datetime

def get_unread_post_count():
    new_messages_count = 0
    user_id = session.get('user_id')

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

    for board in accessible_boards:
        last_viewed = Boardview.query.filter_by(user_id=user_id, board_id=board.id).first()
        if last_viewed:
            new_messages_count += Posts.query.filter(Posts.board_id == board.id, Posts.timestamp > last_viewed.last_viewed_timestamp, Posts.id.notin_(seen_post_ids)).count()
        else:
            new_messages_count += Posts.query.filter_by(board_id=board.id).filter(Posts.id.notin_(seen_post_ids)).count()

    return new_messages_count

class NavBarInfo:
    def __init__(self, username, theme, messageCount, boardCount, healthState):
        self.username = username
        self.theme = theme
        self.messageCount = messageCount
        self.boardCount = boardCount
        self.healthState = healthState

    def __init__(self):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        self.username = user.username
        self.theme = user.ui_style
        self.messageCount = len(Messages.query.filter_by(receiver_id=session['user_id'], isread=None).all())
        self.boardCount = get_unread_post_count()
        self.healthState = user.wound