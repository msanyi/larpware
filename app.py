# this is the beginning of app.py
import os
from flask import Flask  # Import the Flask framework
from database import db  # Import the 'db' object from the 'database' module
from admin import admin  # Import the 'admin' blueprint
from admin_app import admin_blueprint
from user_app import user_blueprint
from flask import render_template
from flask_apscheduler import APScheduler
from combat import setup_ic_scheduler, setup_restore_node_scheduler
from netrunning import debug_print

combat_scheduler = APScheduler()


def create_app():  # Function to create the Flask application
    application = Flask(__name__)  # Create a Flask application instance and name it 'application'

    sql_url = os.getenv("SQL_URL", "localhost")
    sql_user = os.getenv("SQL_USER", "root")
    sql_pass = os.getenv("SQL_PASS", "123qwe")

    # Configure the database connection URI
    application.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{sql_user}:{sql_pass}@{sql_url}/cyberpunk_larpware?charset=utf8mb4'
    application.secret_key = 'your secret key'

    db.init_app(application)  # Initialize the database with the Flask application

    with application.app_context():
        from auth import user_auth, admin_auth
        from transactions import transactions  # Import the 'transactions' blueprint module
        application.register_blueprint(user_auth)  # Register the 'user_auth' blueprint
        application.register_blueprint(user_blueprint)
        application.register_blueprint(transactions)  # Register the 'transactions' blueprint with the Flask application
        application.register_blueprint(admin)  # Register the 'admin' blueprint with the Flask application
        application.register_blueprint(admin_auth, url_prefix='/admin')  # Register the 'admin_auth' blueprint
        application.register_blueprint(admin_blueprint, url_prefix='/admin')

        single_run_flag = False  # Flag to keep track of whether tables are created or not

        # Initialize and start the APScheduler
        combat_scheduler.init_app(application)
        combat_scheduler.start()
        setup_ic_scheduler(combat_scheduler, application)
        setup_restore_node_scheduler(combat_scheduler, application)
        application.jinja_env.filters['debug_print'] = debug_print
        
        db.create_all()  # Create the database tables using SQLAlchemy

    @application.route('/routes')
    def list_routes():
        routes = []
        for rule in application.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "route": str(rule)
            })
        return render_template('routes.html', routes=routes)

    return application


app = create_app()  # Create the Flask application using the 'create_app' function

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True, host='0.0.0.0', port=5000)  # Run the Flask application in debug mode on port 5000
# this is the end of app.py
