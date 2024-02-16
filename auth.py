# this is the beginning of auth.py
from flask import request, session, redirect, url_for, jsonify, Blueprint, render_template, flash
from werkzeug.security import check_password_hash
from database import User


user_auth = Blueprint('user_auth', __name__)
admin_auth = Blueprint('admin_auth', __name__)
# print("auth.py called")


@user_auth.route('/login', methods=['POST', 'GET'])
def user_login():
    print("auth.py user login route started")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Missing login credentials!', 'error')
            return render_template('user_login.html')

        user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password, password):
            flash('Incorrect login credentials!', 'error')
            return render_template('user_login.html')

        # Store user data in the session
        session['user_id'] = user.id
        session['username'] = user.username
        session['balance'] = user.balance
        session['is_admin'] = user.is_admin
        session['citynet'] = user.citynet
        session['is_netrunner'] = user.is_netrunner
        session['is_fixer'] = user.is_fixer
        session['logged_in'] = True
        session.modified = True
        print("auth.py successful login, session data stored")

        if user.passchanged:
            print("auth.py password already changed")
            # if password is already changed, redirect to home page
            return redirect(url_for('user_app.home'))
        else:
            print("auth.py first password change")
            # if password is not changed yet, redirect to change password page
            return redirect(url_for('user_app.change_password'))

    elif request.method == 'GET':
        # return your login form
        return render_template('user_login.html')


@admin_auth.route('/login', methods=['POST', 'GET'])
def admin_login():
    print("auth.py admin login route started")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print("username imput:", username)
        print("password imput:", password)

        if not username or not password:
            flash('Missing login credentials!', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        print("user: user", user)

        if user is None or not check_password_hash(user.password, password):
            flash('Incorrect login credentials!', 'error')
            return render_template('login.html')
        
        if user.is_admin == False:
            flash('Insufficient authorization!', 'error')
            return render_template('login.html')

        # Store user data in the session
        session['user_id'] = user.id
        session['username'] = user.username
        session['balance'] = user.balance
        session['is_admin'] = user.is_admin
        session['citynet'] = user.citynet
        session['is_netrunner'] = user.is_netrunner
        session['is_fixer'] = user.is_fixer
        session['logged_in'] = True
        session.modified = True
        print("auth.py successful login, session data stored")

        if user.passchanged:
            print("auth.py password already changed")
            # if password is already changed, redirect to home page
            return redirect(url_for('admin_app.admin_home'))
        else:
            print("auth.py first password change")
            # if password is not changed yet, redirect to change password page
            return redirect(url_for('admin_app.change_password'))

    elif request.method == 'GET':
        # return your login form
        return render_template('login.html')
# this is the end of auth.py
