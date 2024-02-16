# this is the beginning of user_user_blueprint.py
from flask import render_template, request, session, redirect, url_for, flash, Blueprint, jsonify
from database import db, User, Friendship, Messages, File, Inventory, App
from messaging_app import messaging_app
from scanner import scanner_app
from werkzeug.security import generate_password_hash, check_password_hash
from inventory import inventory_app
from auth import user_auth
from netrunning import netrunning_blueprint
from healthmonitor import health_monitor_app
from ssecfg import sse_blueprint
from flask_cors import CORS
from boards import boards_app
from envelopes import envelopes_app, getEnvelopeCount, getUnopenedEnvelopeCount
from market import client_market_app
from user_settings import user_settings_app
from werkzeug.serving import WSGIRequestHandler
from werkzeug.wrappers import Response
from transactions import make_transaction
from navbar import NavBarInfo
import requests


user_blueprint = Blueprint('user_app', __name__, template_folder='templates')

CORS(user_blueprint)  # This will allow all origins. You can also be specific: CORS(app, origins=["http://127.0.0.1:5002"])

user_blueprint.register_blueprint(user_auth)
user_blueprint.register_blueprint(messaging_app)
user_blueprint.register_blueprint(scanner_app)
user_blueprint.register_blueprint(inventory_app)
user_blueprint.register_blueprint(netrunning_blueprint, url_prefix='/netrunning')
user_blueprint.register_blueprint(sse_blueprint)
user_blueprint.register_blueprint(boards_app)
user_blueprint.register_blueprint(client_market_app)
user_blueprint.register_blueprint(envelopes_app)
user_blueprint.register_blueprint(health_monitor_app)
user_blueprint.register_blueprint(user_settings_app)


@user_blueprint.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if current_password, new_password, and confirm_password are not None
        if not all([current_password, new_password, confirm_password]):
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('user_app.change_password'))

        user = User.query.filter_by(id=session['user_id']).first()

        if not check_password_hash(user.password, current_password):
            flash('Invalid current password', 'error')
            return redirect(url_for('user_app.change_password'))

        if new_password != confirm_password:
            flash('New password and confirm password do not match', 'error')
            return redirect(url_for('user_app.change_password'))

        user.password = generate_password_hash(new_password)
        user.passchanged = True
        db.session.commit()

        flash('Your password has been updated!', 'success')
        return redirect(url_for('user_app.home'))

    return render_template('change_password.html')

@user_blueprint.route('/', methods=['GET'])
def root_url():
    return redirect(url_for('user_app.home'))

@user_blueprint.route('/home', methods=['GET'])
def home():
    if not session.get('logged_in'):
        return redirect(url_for('user_auth.user_login'))
    return render_template('home.html', headerinfo=NavBarInfo(), envelopeCount=getEnvelopeCount(), unopenedEnvelopeCount=getUnopenedEnvelopeCount())


@user_blueprint.route('/account', methods=['GET', 'POST'])
def account():
    print("account path called")
    if not session.get('logged_in'):
        return redirect(url_for('user_auth.user_login'))

    if request.method == 'POST':
        print("method: POST")
        if 'add_user' in request.form:
            friend_citynet = request.form.get('new_user_citynet')
            friend = User.query.filter_by(citynet=friend_citynet).first()
            # Check if friend is valid and not the same as the user
            if friend and friend.id != session['user_id']:
                user = User.query.filter_by(id=session['user_id']).first()
                user.add_friend(friend)  # Add friend using the add_friend method
                db.session.commit()
                # Deselect the user after adding a known user
                session.pop('target_user_id', None)
                session.pop('target_username', None)

    friendships = Friendship.query.filter_by(user_id=session['user_id']).all()
    known_users = []
    for friendship in friendships:
        friend = User.query.filter_by(id=friendship.friend_id).first()
        if "Architecture Watchdog" not in friend.username:  # Check if the username doesn't contain the substring
            known_users.append({'id': friend.id, 'citynet': friend.citynet, 'username': friend.username})
    
    known_users = sorted(known_users, key=lambda d: d['username']) 

    user = User.query.filter_by(id=session['user_id']).first()
    if user:
        session['balance'] = user.balance

    return render_template('account.html',
                           user_id=session.get('user_id'),
                           citynet=session.get('citynet'),
                           username=session.get('username'),
                           balance=session.get('balance'),
                           known_users=known_users,
                           target_username=session.get('target_username', ''),
                           amount=session.get('amount', 0), 
                           headerinfo=NavBarInfo())



@user_blueprint.route('/scanner_redirect', methods=['GET'])  # Change the route to avoid overlap
def scanner_redirect():  # Rename the function for clarity
    if not session.get('logged_in'):
        return redirect(url_for('user_auth.user_login'))
    return redirect(url_for('user_app.scanner_app.scanner_route'))  # Redirect to the desired function


class GracefulErrorHandler(WSGIRequestHandler):
    def handle_error(self):
        if isinstance(self.exception, ConnectionAbortedError):
            self.server.log('info', 'Client disconnected prematurely.')
        else:
            super().handle_error()

@user_blueprint.route('/api/send_app', methods=['POST'])
def send_app():
    data = request.json
    app_id = data['appId']
    sender_id = int(data['senderId'])
    target_id = int(data['targetUserId'])

    if sender_id != session['user_id']:
        return jsonify({'error': 'fuckery detected'}), 403

    sender = User.query.get(sender_id)

    # Fetch the file
    app = App.query.get(app_id)
    if not app:
        return jsonify({'error': 'App not found'}), 404

    # Check if the sender has the file in their inventory
    sender_inventory = Inventory.query.filter_by(user_id=sender_id, app_id=app_id).first()
    if not sender_inventory:
        return jsonify({'error': 'Sender does not have the app in their inventory'}), 404

    # Check if the target user exists
    target_user = User.query.get(target_id)
    if not target_user:
        return jsonify({'error': 'Target user not found'}), 404

    # Remove the file from the sender's inventory
    db.session.delete(sender_inventory)

    # Add the file to the target user's inventory
    target_inventory = Inventory(user_id=target_id, app_id=app_id)
    db.session.add(target_inventory)

    db.session.commit()

    message_content = f"{sender.username} sent {target_user.username} an app: {app.name}"
    new_message = Messages(sender_id=sender.id, receiver_id=target_user.id, messagecontent=message_content, is_system=True)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({'success': True, 'message': 'App transferred successfully!'}), 200

@user_blueprint.route('/api/send_file', methods=['POST'])
def send_file():
    data = request.json
    file_id = data['fileId']
    sender_id = int(data['senderId'])
    target_id = int(data['targetUserId'])

    if sender_id != session['user_id']:
        return jsonify({'error': 'fuckery detected'}), 403

    sender = User.query.get(sender_id)

    # Fetch the file
    file = File.query.get(file_id)
    if not file:
        return jsonify({'error': 'File not found'}), 404

    # Check if the sender has the file in their inventory
    sender_inventory = Inventory.query.filter_by(user_id=sender_id, file_id=file_id).first()
    if not sender_inventory:
        return jsonify({'error': 'Sender does not have the file in their inventory'}), 404

    # Check if the target user exists
    target_user = User.query.get(target_id)
    if not target_user:
        return jsonify({'error': 'Target user not found'}), 404

    # Remove the file from the sender's inventory
    db.session.delete(sender_inventory)

    # Add the file to the target user's inventory
    target_inventory = Inventory(user_id=target_id, file_id=file_id)
    db.session.add(target_inventory)

    db.session.commit()

    message_content = f"{sender.username} sent {target_user.username} a file: {file.name}"
    new_message = Messages(sender_id=sender.id, receiver_id=target_user.id, messagecontent=message_content, is_system=True)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({'success': True, 'message': 'File transferred successfully!'}), 200


def application(environ, start_response):
    # ...to omit a disturbing error message when something on my PC broke the connection
    response = Response('something on my PC broke the connection, just ignore this')
    return response(environ, start_response)

# this is the end of user_user_blueprint.py
