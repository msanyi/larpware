# this is the beginning of admin.py
# This file contains server-side logic
from flask import Blueprint, request, jsonify,  redirect, flash, url_for, session  # Import the necessary modules from Flask
from werkzeug.security import generate_password_hash
from database import User, db, UserOrganization, Organizations  # Import the 'User' model from the 'database' module
from sqlalchemy.exc import SQLAlchemyError
import random

admin = Blueprint('admin', __name__)  # Create a blueprint named 'admin'


@admin.route('/admin/add_user', methods=['POST'])
# This route receives requests to create a new user and performs the server-side logic to add this user to the database.
def add_user():
    user = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or user is None or user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    
    try:
        username = request.json.get('new_username')
        password = request.json.get('new_password')
        is_admin = request.json.get('is_admin', False)
        is_netrunner = request.json.get('is_netrunner', False)
        is_fixer = request.json.get('is_fixer', False)
        is_npc = request.json.get('is_npc', False)

        print('is npc', is_npc)

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, is_admin=is_admin, is_netrunner=is_netrunner, is_fixer=is_fixer, citynet=generate_citynet(), is_npc=is_npc)

        db.session.add(new_user)
        db.session.commit()
        selected_org_id = request.json.get('organization_id')  # Get the organization ID from the request
        print("selected_org_id: ", selected_org_id)
        if selected_org_id:
            user_org = UserOrganization(user_organization_id=new_user.id, organization_id=selected_org_id)
            print("user_org: ", user_org)
            db.session.add(user_org)
            db.session.commit()
        return jsonify(message="User added successfully"), 200  # Return a JSON response indicating success
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An error occurred: ' + str(e)}), 500


@admin.route('/modify_balance', methods=['POST'])
def modify_balance():
    admin = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or admin is None or admin.is_admin == False:
        return redirect(url_for('admin_app.login'))
    
    user_id = request.form.get('user_id')
    new_balance = request.form.get('new_balance')

    if not user_id or not new_balance:
        return jsonify({'error': 'User ID and new balance are required'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.balance = new_balance
    db.session.commit()
    flash("Balance updated successfully")
    return redirect(url_for('admin_app.admin'))

@admin.route('/org_add', methods=['POST'])
def org_add():
    admin = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or admin is None or admin.is_admin == False:
        return redirect(url_for('admin_app.login'))
    
    user_id = request.form.get('user_id')
    org_id = request.form.get('organization_id')

    if not user_id or not org_id:
        return jsonify({'error': 'User ID and new balance are required'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_org = UserOrganization(user_organization_id=user_id, organization_id=org_id)
    print("user_org: ", user_org)
    db.session.add(user_org)
    db.session.commit()
    
    flash("User added to org successfully")
    return redirect(url_for('admin_app.admin'))

def generate_citynet():
    while True:
        citynet = random.randint(1000000, 9999999)
        user = User.query.filter_by(citynet=citynet).first()
        if not user:
            return citynet

# this is the end of admin.py
