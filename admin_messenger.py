# beginning of messaging_app.py
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for  # redirect, url_for removed, not used
from database import db, User, Messages
from sqlalchemy import or_, and_
from datetime import datetime
from navbar import NavBarInfo

admin_messaging_app = Blueprint('admin_messaging_app', __name__)


@admin_messaging_app.route('/send_message', methods=['POST'])
def send_message():
    user = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or user is None or user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    
    print("admin send_message called")
    data = request.get_json()
    from_id = data.get('from')
    to_id = data.get('to')
    message_content = data.get('message')
    new_message = Messages(sender_id=from_id, receiver_id=to_id, messagecontent=message_content)
    db.session.add(new_message)
    db.session.commit()
    return jsonify({'message': 'Message sent successfully.'}), 200

@admin_messaging_app.route('/messages/load/<int:npc_id>/<int:contact_id>', methods=['GET'])
def load_messages_with_contact(npc_id, contact_id):
    print("loading message list between npc", npc_id, "and", contact_id)
    current_user = User.query.get(session['user_id'])  # Get the current user
    if 'logged_in' not in session or not session['logged_in'] or current_user is None or current_user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    
    messages = Messages.query.filter(or_(and_(Messages.sender_id == npc_id, Messages.receiver_id == contact_id),
                                         and_(Messages.sender_id == contact_id, Messages.receiver_id == npc_id))).order_by(Messages.timesent.desc()).all()
    message_list = []
    for message in messages:
        if message.isread is None and message.sender_id != npc_id:
            message.isread = datetime.utcnow()
        message_list.append({'message_id': message.id, 'sender': message.sender.id, 'messagecontent': message.messagecontent, 'timesent': message.timesent, 'system':message.is_system})
    db.session.commit()
    return jsonify({'messages': message_list,'loaded': datetime.utcnow().isoformat()}), 200

@admin_messaging_app.route('/messages/poll', methods=['POST'])
def poll_chat():
    data = request.get_json()
    response_list = []
    for chat in data:
        if chat.get('type') == 'Card':
            npc_id = chat.get('npc')
            since = chat.get("since")
            sinceDatetime = datetime.fromisoformat(since)
            print("checking if there was a new message since",since)
            message = Messages.query.filter(and_(Messages.receiver_id == npc_id, Messages.timesent > sinceDatetime)).first()
            if message is not None:
                response_list.append(True)
            else:
                response_list.append(False)
        elif chat.get('type') == 'Chat':
            npc_id = chat.get('npc')
            contact_id = chat.get('contact')
            since = chat.get("since")
            sinceDatetime = datetime.fromisoformat(since)
            print("checking if there was a new message between npc",npc_id,"and",contact_id,"since",since)
            message = Messages.query.filter(or_(and_(Messages.sender_id == npc_id, Messages.receiver_id == contact_id),
                                                and_(Messages.sender_id == contact_id, Messages.receiver_id == npc_id))).order_by(Messages.timesent.desc()).first()
            if message is not None and message.timesent > sinceDatetime:
                response_list.append(True)
            else:
                response_list.append(False)
        else:
            response_list.append(False)
    return jsonify(response_list), 200

@admin_messaging_app.route('/messages', methods=['GET'])
def messages_page():
    current_user = User.query.get(session['user_id'])  # Get the current user
    if 'logged_in' not in session or not session['logged_in'] or current_user is None or current_user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    print("current_user: ", current_user)
    npc_users = User.query.filter(User.is_npc == True).order_by(User.username).all()
    
    return render_template('admin_messenger.html',
                           npc_users=npc_users)

@admin_messaging_app.route("/messages/friendlist/<int:npc_id>", methods=['GET'])
def load_friends_list(npc_id):
    current_user = User.query.get(session['user_id'])  # Get the current user
    if 'logged_in' not in session or not session['logged_in'] or current_user is None or current_user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    npc_user = User.query.get(npc_id)
    friend_ids = [friendship.friend_id for friendship in npc_user.friends]
    friends = User.query.filter(User.id.in_(friend_ids), ~User.username.like("%Architecture Watchdog%")).order_by(User.username).all()
    friend_list = []
    for friend in friends:
        friend_list.append({"id":friend.id, "username":friend.username})
    return jsonify(friend_list), 200

@admin_messaging_app.route('/messages/load-cards/<int:npc_id>', methods=['GET'])
def load_message_cards(npc_id):
    current_user = User.query.get(session['user_id'])  # Get the current user
    if 'logged_in' not in session or not session['logged_in'] or current_user is None or current_user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    npc_user = User.query.get(npc_id)
    print("current_user: ", npc_user)
    friend_ids = [friendship.friend_id for friendship in npc_user.friends]
    message_boxes = []
    print(friend_ids)
    for friend_id in friend_ids:
        message = Messages.query.filter(or_(
            and_(Messages.sender_id == npc_id, Messages.receiver_id == friend_id),
            and_(Messages.sender_id == friend_id, Messages.receiver_id == npc_id))).order_by(Messages.timesent.desc()).first()
        if message is not None:
            unread_from_friend = Messages.query.filter(
                and_(Messages.sender_id == friend_id, Messages.receiver_id == npc_id), Messages.isread==None).count()
            message_boxes.append({'message_id': message.id, 'sender_id': message.sender_id, 'sender_name':message.sender.username,'receiver_id': message.receiver_id, 'receiver_name':message.receiver.username, 'message_content': message.messagecontent, 'time_sent': message.timesent, 'unreads': unread_from_friend})
    
    message_boxes = sorted(message_boxes, key=lambda d: d['time_sent'], reverse=True)
    print(message_boxes)
    return jsonify({'messages': message_boxes,'loaded': datetime.utcnow().isoformat()}), 200



# end of messaging_app.py
