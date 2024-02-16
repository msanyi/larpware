from flask import Blueprint, jsonify, render_template, redirect, url_for, session, request
from database import User, db
from navbar import NavBarInfo

health_monitor_app = Blueprint('health_monitor_app', __name__)

def get_display_state(health_state):
    if health_state == 'wounded':
        return "WOUNDED"
    elif health_state == 'dying':
        return "DYING"
    elif health_state == 'dead':
        return "FLATLINED"
    else:
        return "OK"


@health_monitor_app.route('/health', methods=['GET'])
def health_monitor():
    if not session.get('user_id'):
        return redirect(url_for('user_auth.user_login'))

    user = User.query.filter_by(id=session['user_id']).first()
    health_state = user.wound
    display_state = get_display_state(health_state)
    armor = user.armor_value
    reflex = user.reflex_value
    
    return render_template('health_monitor.html',
                           health=health_state,
                           display_state=display_state,
                           armor = armor,
                           reflex = reflex,
                           headerinfo=NavBarInfo())

@health_monitor_app.route('/health/remove', methods=['POST'])
def decrease_health_state():
    if not session.get('user_id'):
       return redirect(url_for('user_auth.user_login'))

    user = User.query.filter_by(id=session['user_id']).first()
    match user.wound:
        case "unhurt":
            user.wound = "wounded"
        case "wounded":
            user.wound = "dying"
        case "dying":
            user.wound = "dead"
        case "dead":
            user.wound = "dead"
    db.session.commit()

    return redirect(url_for("user_app.health_monitor_app.health_monitor"))

@health_monitor_app.route('/health/add', methods=['POST'])
def increase_health_state():
    if not session.get('user_id'):
       return redirect(url_for('user_auth.user_login'))

    user = User.query.filter_by(id=session['user_id']).first()
    match user.wound:
        case "unhurt":
            user.wound = "unhurt"
        case "wounded":
            user.wound = "unhurt"
        case "dying":
            user.wound = "wounded"
        case "dead":
            user.wound = "dying"
    db.session.commit()

    return redirect(url_for("user_app.health_monitor_app.health_monitor"))

@health_monitor_app.route('/health/set', methods=['POST'])
def set_armor_reflex():
    if not session.get('user_id'):
       return redirect(url_for('user_auth.user_login'))

    data = request.get_json()
    armor = int(data.get('armor', 0))
    reflex = int(data.get('reflex', 0))

    user = User.query.filter_by(id=session['user_id']).first()
    user.armor_value = armor
    user.reflex_value = reflex
    db.session.commit()

    return jsonify({'success':'true'}), 200