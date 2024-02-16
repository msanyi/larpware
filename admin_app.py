# this is the beginning of admin_admin_blueprint.py
# This file contains the admin dashboard that interacts with the server via HTTP requests.
import requests  # Import the requests module for making HTTP requests
from flask import render_template, request, redirect, url_for, session, flash, Response
# Import the necessary modules from Flask
from admin_networkcreator_app import network_creator
from admin_netmod_app import admin_netmod_app
from database import User, UserOrganization, Organizations
from werkzeug.security import check_password_hash
from admin_market import admin_market_app
from admin_couriertasks import admin_couriertasks_app
from admin_qrmanager import admin_qrmanager_app
from admin_envelopes import admin_envelopes_app
from admin_messenger import admin_messaging_app
from flask import Blueprint, jsonify
from admin import add_user
from datetime import datetime
import json

admin_blueprint = Blueprint('admin_app', __name__, template_folder='templates')
admin_blueprint.register_blueprint(network_creator, url_prefix='/admin')
admin_blueprint.register_blueprint(admin_netmod_app, url_prefix='/admin')
admin_blueprint.register_blueprint(admin_market_app)
admin_blueprint.register_blueprint(admin_couriertasks_app)
admin_blueprint.register_blueprint(admin_qrmanager_app)
admin_blueprint.register_blueprint(admin_envelopes_app)
admin_blueprint.register_blueprint(admin_messaging_app)

@admin_blueprint.route('/admin_home', methods=['GET'])
def admin_home():
    print("admin_home called")
    user = User.query.filter_by(id=session['user_id']).first()

    if 'logged_in' not in session or not session['logged_in'] or user is None or user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    return render_template('admin_home.html')


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    print("admin_app.py login called")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return 'Username and password are required', 400

        user = User.query.filter_by(username=username).first()

        if user and user.is_admin and check_password_hash(user.password, password):
            session['logged_in'] = True
            return redirect(url_for('admin_blueprint.admin_home'))
        else:
            return 'Invalid credentials', 401

    return render_template('login.html')


@admin_blueprint.route('/admin/users_balances', methods=['GET'])
def admin():
    print("admin_app.py admin route called")
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('admin_app.auth.login'))

    organizations = Organizations.query.all()
    org_full_list = [{"id": org.id, "name": org.orgname} for org in organizations]
    org_dict = {}
    for org in organizations:
        org_dict[org.id] =org.orgname

    print(org_dict)
    error_message = ''
    users = User.query.all()
    userdata = []
    for user in users:
        user_orgs = UserOrganization.query.filter(UserOrganization.user_organization_id==user.id, UserOrganization.endtime == None).all()
        org_list = []
        for user_org in user_orgs:
            org_list.append(org_dict[user_org.organization_id])
        user_temp_orgs = UserOrganization.query.filter(UserOrganization.user_organization_id==user.id, UserOrganization.endtime > datetime.utcnow()).all()
        temp_org_list = []
        for user_org in user_temp_orgs:
            temp_org_list.append(org_dict[user_org.organization_id])
        userdata.append({
            'id':user.id,
            'username':user.username,
            'citynet':user.citynet,
            'passchanged':user.passchanged,
            'balance':user.balance,
            'is_admin':user.is_admin,
            'is_npc':user.is_npc,
            'is_fixer':user.is_fixer,
            'is_netrunner':user.is_netrunner,
            'wound':user.wound,
            'organizations':org_list,
            'temp_organizations':temp_org_list
        })
        
    return render_template('users_balances.html', users=userdata, org_list=org_full_list, error_message=error_message)


@admin_blueprint.route('/admin/network-creator', methods=['GET'])
def admin_network_creator():
    # The route that will direct to the network creator page
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('admin_app.auth.login'))
    return render_template('admin_networkcreator.html')


@admin_blueprint.route('/admin/network_modifier', methods=['GET'])
def admin_network_modifier():
    # The route that will direct to the network modifier page
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('admin_app.auth.login'))
    return render_template('admin_networkmodifier.html')

# this is the end of admin_admin_blueprint.py
