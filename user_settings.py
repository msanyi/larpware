from flask import Blueprint, jsonify, render_template, redirect, url_for, session, request
from database import User, db
from navbar import NavBarInfo

user_settings_app = Blueprint('user_settings_app', __name__)

@user_settings_app.route('/settings', methods=['GET'])
def user_settings():
    if not session.get('user_id'):
        return redirect(url_for('user_auth.user_login'))
    
    return render_template('user_settings.html',
                           headerinfo=NavBarInfo())

@user_settings_app.route('/settings/theme/set', methods=['POST'])
def set_theme():
    if not session.get('user_id'):
       return redirect(url_for('user_auth.user_login'))

    data = request.get_json()
    theme = data.get('theme', "console-green")

    user = User.query.filter_by(id=session['user_id']).first()
    user.ui_style = theme
    db.session.commit()

    return jsonify({'success':'true'}), 200