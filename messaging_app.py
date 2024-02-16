# beginning of messaging_app.py
from flask import Blueprint, request, jsonify, session, render_template  # redirect, url_for removed, not used
from database import db, User, Messages
from sqlalchemy import or_, and_
from datetime import datetime
from navbar import NavBarInfo

messaging_app = Blueprint('messaging_app', __name__)


@messaging_app.route('/send_message', methods=['POST'])
def send_message():
    print("send_message called")
    receiver_username = request.form.get('receiver_username')
    message_content = request.form.get('message')
    receiver = User.query.filter_by(username=receiver_username).first()
    if receiver:
        new_message = Messages(sender_id=session['user_id'], receiver_id=receiver.id, messagecontent=message_content)
        db.session.add(new_message)
        db.session.commit()
        return jsonify({'message': 'Message sent successfully.'}), 200
    else:
        return jsonify({'error': 'Receiver not found.'}), 400


@messaging_app.route('/messages/<int:contact_id>', methods=['GET'])
def chat_with_contact(contact_id):
    current_user = User.query.get(session['user_id'])  # Get the current user
    friend_ids = [friendship.friend_id for friendship in current_user.friends]
    print(friend_ids)
    if contact_id not in friend_ids:
        return jsonify({'error':'Permission denied'}), 403
    current_contact = User.query.get(contact_id)

    return render_template('messages_chat.html',
                           username=current_user.username,
                           contact=current_contact,
                           headerinfo=NavBarInfo())

@messaging_app.route('/messages/load/<int:contact_id>', methods=['GET'])
def load_messages_with_contact(contact_id):
    print("loading message list with user id",contact_id)
    current_user = User.query.get(session['user_id'])  # Get the current user
    friend_ids = [friendship.friend_id for friendship in current_user.friends]
    if contact_id not in friend_ids:
        return jsonify({'error':'Would you kindly please fuck off'}), 403
    
    messages = Messages.query.filter(or_(and_(Messages.sender_id == session['user_id'], Messages.receiver_id == contact_id),and_(Messages.sender_id == contact_id, Messages.receiver_id == session['user_id']))).order_by(Messages.timesent.desc()).all()
    message_list = []
    for message in messages:
        if message.isread is None and message.sender_id != session['user_id']:
            message.isread = datetime.utcnow()
        message_list.append({'message_id': message.id, 'sender': message.sender.username, 'messagecontent': message.messagecontent, 'timesent': message.timesent, 'system':message.is_system})
    db.session.commit()
    return jsonify({'messages': message_list,'loaded': datetime.utcnow().isoformat()}), 200

@messaging_app.route('/messages/poll', methods=['GET'])
def poll_chat():
    args = request.args
    contact_id = args.get("contact_id", default=0, type=int)
    since = args.get("since", default="2023-01-01T00:00:01.545806", type=str)
    sinceDatetime = datetime.fromisoformat(since)
    print("checking if there was a new message with",contact_id,"since",since)
    message = Messages.query.filter(or_(and_(Messages.sender_id == session['user_id'], Messages.receiver_id == contact_id),and_(Messages.sender_id == contact_id, Messages.receiver_id == session['user_id']))).order_by(Messages.timesent.desc()).first()
    if message is not None and message.timesent > sinceDatetime:
        return jsonify({'reload_required': True})
    else:
        return jsonify({'reload_required': False})

@messaging_app.route('/messages', methods=['GET'])
def messages_page():
    current_user = User.query.get(session['user_id'])  # Get the current user
    print("current_user: ", current_user)
    friend_ids = [friendship.friend_id for friendship in current_user.friends]
    friends = User.query.filter(User.id.in_(friend_ids), ~User.username.like("%Architecture Watchdog%")).order_by(User.username).all()
    message_boxes = []
    for friend_id in friend_ids:
        message = Messages.query.filter(or_(
            and_(Messages.sender_id == session['user_id'], Messages.receiver_id == friend_id),
            and_(Messages.sender_id == friend_id, Messages.receiver_id == session['user_id']))).order_by(Messages.timesent.desc()).first()
        if message is not None:
            unread_from_friend = Messages.query.filter(
            and_(Messages.sender_id == friend_id, Messages.receiver_id == session['user_id']), Messages.isread==None).count()
            message_boxes.append({'message_id': message.id, 'sender_id': message.sender_id, 'sender_name':message.sender.username,'receiver_id': message.receiver_id, 'receiver_name':message.receiver.username, 'message_content': message.messagecontent, 'time_sent': message.timesent, 'unreads': unread_from_friend})
    
    message_boxes = sorted(message_boxes, key=lambda d: d['time_sent'], reverse=True)
    print(message_boxes)
    return render_template('messages_list.html',
                           friends=friends,
                           message_boxes=message_boxes,
                           username=current_user.username,
                           headerinfo=NavBarInfo())

@messaging_app.route('/messages/load-cards', methods=['GET'])
def load_message_cards():
    current_user = User.query.get(session['user_id'])  # Get the current user
    print("current_user: ", current_user)
    friend_ids = [friendship.friend_id for friendship in current_user.friends]
    friends = User.query.filter(User.id.in_(friend_ids), ~User.username.like("%Architecture Watchdog%")).order_by(User.username).all()
    message_boxes = []
    for friend_id in friend_ids:
        message = Messages.query.filter(or_(
            and_(Messages.sender_id == session['user_id'], Messages.receiver_id == friend_id),
            and_(Messages.sender_id == friend_id, Messages.receiver_id == session['user_id']))).order_by(Messages.timesent.desc()).first()
        if message is not None:
            unread_from_friend = Messages.query.filter(
            and_(Messages.sender_id == friend_id, Messages.receiver_id == session['user_id']), Messages.isread==None).count()
            message_boxes.append({'message_id': message.id, 'sender_id': message.sender_id, 'sender_name':message.sender.username,'receiver_id': message.receiver_id, 'receiver_name':message.receiver.username, 'message_content': message.messagecontent, 'time_sent': message.timesent, 'unreads': unread_from_friend})
    
    message_boxes = sorted(message_boxes, key=lambda d: d['time_sent'], reverse=True)
    print(message_boxes)
    return jsonify({'messages': message_boxes,'loaded': datetime.utcnow().isoformat()}), 200

@messaging_app.route('/messages/poll-cards', methods=['GET'])
def poll_cards():
    args = request.args
    since = args.get("since", default="", type=str)
    sinceDatetime = datetime.fromisoformat(since)
    print("checking if there was a new message since",since)
    message = Messages.query.filter(and_(Messages.receiver_id == session['user_id'], Messages.timesent > sinceDatetime)).first()
    if message is not None:
        return jsonify({'reload_required': True})
    else:
        return jsonify({'reload_required': False})

# end of messaging_app.py
