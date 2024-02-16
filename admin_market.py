from flask import Blueprint, render_template, request, flash, jsonify, session, redirect, url_for
from database import db, Digitalmarketlisting, Organizationavailability, App, AppType, Organizations, File, Couriertask, User
import random
from datetime import datetime

admin_market_app = Blueprint('admin_market_app', __name__)


@admin_market_app.route('/market', methods=['GET', 'POST'])
def manage_market():
    user = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or user is None or user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    
    app_types = AppType.query.all()
    organizations = Organizations.query.all()

    # For POST requests (When adding a new item)
    if request.method == 'POST':
        item_type = request.form.get('item_type')

        # If adding an app type item
        if item_type == 'app':
            app_type_id = request.form.get('app_type_id')
            quantity = int(request.form.get('quantity'))
            organizations_selected = request.form.getlist('organizations')  # multi-select returns a list
            price = int(request.form.get('price'))
            valid_from_str=request.form.get('valid_from')
            print("form input, app_type_id: ", app_type_id)
            print("form input, quantity: ", quantity)
            print("form input, organizations_selected: ", organizations_selected)
            print("form input, price: ", price)
            print("form input, valid_from: ", valid_from_str)

            valid_from = None;
            if valid_from_str not in [None, '']:
                valid_from = datetime.fromisoformat(valid_from_str)

            # Create the App entries
            for _ in range(quantity):
                app_type = AppType.query.get(app_type_id)
                app_type_name = app_type.name
                app_name = f"{app_type_name}_{random.randint(1000, 9999)}"
                new_app = App(app_type_id=app_type_id, name=app_name)

                db.session.add(new_app)
                db.session.commit()

                # Create Digital Market Listing for the app
                # Get the market_type from form data. (Assuming you have added it in the client form)
                market_type_selected = request.form.get('market_type')

                # Check if market_type_selected is one of the allowed values.
                if market_type_selected not in ['Public', 'Fixer', 'Darkweb']:
                    # Handle this error, maybe return a response or raise an exception
                    raise ValueError("Invalid market type selected!")

                item_desc = app_type.description
                new_listing = Digitalmarketlisting(name=app_type_name,
                                                   price=price,
                                                   listing_type='App',
                                                   description=item_desc,
                                                   market_type=market_type_selected,
                                                   app_id=new_app.id,
                                                   valid_from=valid_from)

                db.session.add(new_listing)
                db.session.commit()

                # Create Organizationavailability entries
                for org_id in organizations_selected:
                    new_availability = Organizationavailability(listing_id=new_listing.id, organization_id=int(org_id))
                    db.session.add(new_availability)
                    db.session.commit()

            flash("App items successfully added to the market!", "success")

        elif item_type == 'file':
            print("file type path")
            file_name = request.form.get('file_name')
            file_content = request.form.get('file_content')
            price = int(request.form.get('price'))
            organizations_selected = request.form.getlist('organizations')

            valid_from = None;
            if valid_from_str not in [None, '']:
                valid_from = datetime.fromisoformat(valid_from_str)

            # Create the File entry
            new_file = File(name=file_name, content=file_content)

            db.session.add(new_file)
            db.session.commit()

            # Create Digital Market Listing for the file
            market_type_selected = request.form.get('market_type')

            if market_type_selected not in ['Public', 'Fixer', 'Darkweb']:
                raise ValueError("Invalid market type selected!")

            new_listing = Digitalmarketlisting(name=file_name,
                                               price=price,
                                               listing_type='File',
                                               description=f"File: {file_name}",
                                               market_type=market_type_selected,
                                               file_id=new_file.id,
                                               valid_from=valid_from)

            db.session.add(new_listing)
            db.session.commit()

            # Create Organizationavailability entries for the file
            for org_id in organizations_selected:
                new_availability = Organizationavailability(listing_id=new_listing.id, organization_id=int(org_id))
                db.session.add(new_availability)
                db.session.commit()

            flash("File item successfully added to the market!", "success")

        elif item_type == 'physical':
            item_name = request.form.get('item_name')
            description = request.form.get('description')
            quantity = int(request.form.get('quantity'))
            price = int(request.form.get('price'))
            market_type_selected = request.form.get('market_type')
            organizations_selected = request.form.getlist('organizations')

            valid_from = None;
            if valid_from_str not in [None, '']:
                valid_from = datetime.fromisoformat(valid_from_str)


            # Check if market_type_selected is one of the allowed values.
            if market_type_selected not in ['Public', 'Fixer', 'Darkweb']:
                raise ValueError("Invalid market type selected!")

            # Create Digital Market Listing for the physical item.
            for _ in range(quantity):
                new_listing = Digitalmarketlisting(
                    name=item_name,
                    price=price,
                    listing_type='Physical Item',
                    description=description,
                    market_type=market_type_selected,
                    valid_from=valid_from
                )
                db.session.add(new_listing)
                db.session.commit()

                # Create Organizationavailability entries for the physical item
                for org_id in organizations_selected:
                    new_availability = Organizationavailability(listing_id=new_listing.id, organization_id=int(org_id))
                    db.session.add(new_availability)
                    db.session.commit()

            flash("Physical items successfully added to the market!", "success")

    # For GET requests (Or after a POST request has been handled)
    courier_listings_ids = [task.listing_id for task in Couriertask.query.all()]
    
    listings = Digitalmarketlisting.query.filter(Digitalmarketlisting.id.notin_(courier_listings_ids)).all()
    

    print("listings for render: ", listings)
    print("app_types for render: ", app_types)
    print("organizations for render: ", organizations)
    return render_template('admin_market.html', listings=listings, app_types=app_types, organizations=organizations, utcnow=datetime.utcnow())


@admin_market_app.route('/market/<int:item_id>', methods=['POST'])
def delete_listing(item_id):
    user = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or user is None or user.is_admin == False:
        return redirect(url_for('admin_app.login'))

    Organizationavailability.query.filter(Organizationavailability.listing_id == item_id).delete()
    Couriertask.query.filter(Couriertask.listing_id == item_id).delete()
    db.session.commit()
    Digitalmarketlisting.query.filter(Digitalmarketlisting.id == item_id).delete()
    db.session.commit()

    return redirect(url_for('admin_app.admin_market_app.manage_market'))