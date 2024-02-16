from flask import Flask, render_template, request, Blueprint, jsonify, redirect, url_for, session
from database import db, Qrcode, Digitalmarketlisting, Organizations, File, App, User
app = Flask(__name__)

admin_qrmanager_app = Blueprint('admin_qrmanager_app', __name__)


@admin_qrmanager_app.route('/qrmanager', methods=['GET'])
def admin_qrmanager():
    user = User.query.filter_by(id=session['user_id']).first()
    if 'logged_in' not in session or not session['logged_in'] or user is None or user.is_admin == False:
        return redirect(url_for('admin_app.login'))
    return render_template('admin_qrmanager.html')

@admin_qrmanager_app.route('/qrmanager/scan', methods=['POST'])
def admin_qrmanager_scan():
    print("admin_qrmanager scan called")
    assigned_data = None
    message = None
    # Get qr_content from POST JSON or GET parameters
    qr_content = None
    content_items  = []

    data = request.get_json()
    qr_content = data.get('qr_content')

    # what this should do:
    # check if there is qr content - otherwise render empty template
    # check if qr content is valid - otherwise throw error and render empty template
    # display current information about assignments
    # in case of network QR, display its info and assignments
    # in case of lock QR, display its info and assignments
    # in case of app QR, pull available apps (which have a digital market listing) and add to template
    # in case of file QR, pull available files (no owner AND no qr assignment) and add to template
    # render template
    
    if qr_content:
        qr_code = Qrcode.query.filter_by(id=qr_content).first()
        print("qr_content: ", qr_content)
        print("qr_code:", qr_code)

        if qr_code:
            print("qr_code: ", qr_code)
            if qr_code.targetid:
                print("qr_code.targetid: ", qr_code.targetid)
                assigned_data = {"targetid": qr_code.targetid}

                # Check the type of the QR code
                if qr_code.qrcodetype == 'inventoryadd_app':
                    print("qr_code.qrcodetype: ", qr_code.qrcodetype)
                    appcode = App.query.get(qr_code.targetid)  # Get the app using targetid
                    if appcode:
                        assigned_data['name'] = appcode.name
                        assigned_data['id'] = appcode.id
                        assigned_data['type'] = 'App'
                        message = f"This is an Data Shard containing the app: {appcode.name}"
                        print("assigned_data for app:", assigned_data)
                    else:
                        message = "This is an empty App Shard."

                elif qr_code.qrcodetype == 'inventoryadd_file':
                    file = File.query.get(qr_code.targetid)  # Get the file using targetid
                    if file:
                        assigned_data['name'] = file.name
                        assigned_data['type'] = 'File'
                        message = f"This is a Data Shard containing the file: {file.name}"
                    else:
                        message = "This is an empty File Shard."

                elif qr_code.qrcodetype == 'inventoryadd_cash':
                    cash = qr_code.targetid or 0
                    assigned_data['name'] = cash
                    assigned_data['type'] = 'Cash'
                    message = f"This is a Data Shard containing a cryptokey worth {cash} €$"

                # Save assigned_data to session
                print("assigned_data for file:", assigned_data)

            qrcodetype = qr_code.qrcodetype
            if qrcodetype == 'accesspoint':
                print("accesspoint path")
                assigned_data['name'] = qr_code.qrcode
                message = "This is a network entry code."

            elif qrcodetype in ['inventoryadd_app', 'inventoryadd_file', 'inventoryadd_cash']:
                print("inventoryadd_file path")
                app_items = Digitalmarketlisting.query.filter_by(
                    listing_type='App').all()
                message = "This is a data shard."
                content_items = [{'id': item.app_id, 'type': 'App', 'name': item.name} for item in app_items]

                taken_item_ids = [code.targetid for code in Qrcode.query.filter(Qrcode.qrcodetype == "inventoryadd_file", Qrcode.targetid != None).all()]
                file_items = File.query.filter(File.original_owner_id.is_(None), File.copied_by_id.is_(None)).all()
                for item in file_items:
                    if item.id not in taken_item_ids:
                        content_items.append({'id': item.id, 'type': 'File', 'name': item.name})

            elif qrcodetype == 'lock':
                print("lock path")
                items = Organizations.query.all()
                content_items = [{'id': org.id, 'name': org.orgname} for org in items]
                organization = Organizations.query.filter_by(id=qr_code.targetid).first()
                message = f"This is a Lock keyed to organization {organization.name}"
                if organization:
                    assigned_data['name'] = organization.orgname
                    assigned_data['type'] = 'Lock'
                else:
                    # Handle the case where no organization is found for the given targetid
                    assigned_data['name'] = "Unknown Organization"


    print("assigned_data sent: ", assigned_data)
    return jsonify({"assigned_data": assigned_data,
                        "items" : content_items,
                        "message" : message,
                        "qrcodetype" : qrcodetype}), 200


@admin_qrmanager_app.route('/qrmanager/set', methods=['POST'])
def qrmanager_set():
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('item_type')
    qrcodetype = data.get('qrcodetype')
    decoded_text = data.get('decoded_text')
    print("update_targetid called")
    print("with item_id: ", item_id)
    print("and qrcodetype: ", qrcodetype)
    print("and decoded_text: ", decoded_text)
    if qrcodetype is None:
        return jsonify(error="qrcodetype is not provided"), 400
    qr_code = Qrcode.query.filter_by(id=decoded_text).first()
    if qr_code:
        qrcode_id = qr_code.id
    else:
        return jsonify(error="QR Code not found"), 404
    
    if qrcodetype in ['inventoryadd_file', 'inventoryadd_app', 'inventoryadd_cash']:
    # If Qrcode is found, update the targetid
        if item_type in ['File']:
            print("inventoryadd_file")
            listing = Digitalmarketlisting.query.filter(Digitalmarketlisting.file_id == item_id).first()
            print("listing: ", listing)
            if listing:            
                db.session.delete(listing)
            qr_code.qrcodetype = 'inventoryadd_file'
        elif item_type in ['App']:
            print("inventoryadd_app path")
            listing = Digitalmarketlisting.query.filter(Digitalmarketlisting.app_id == item_id).first()
            print("listing: ", listing)
            if listing:            
                db.session.delete(listing)
            qr_code.qrcodetype = 'inventoryadd_app'
        else:
            print("inventoryadd_cash path")
            qr_code.qrcodetype = 'inventoryadd_cash'
        qr_code.targetid = item_id
        db.session.commit()

    elif qrcodetype == 'lock':
        print("lock path called")
        org = Organizations.query.get(item_id)
        print("organization found: ", org)
        if not org:
            return jsonify(error="Organization not found"), 404
        # Assuming you also have a qrcode_id available to pass to the update function
        update_qrcode_targetid_lock(qrcode_id, org.id)

    db.session.commit()
    return jsonify({'success':'true'}), 200




def update_qrcode_targetid(qrcode_id, target_id):
    """
    This function updates the targetid of the Qrcode with the given qrcode_id
    to the specified target_id.
    """
    # Find the Qrcode by qrcode_id
    qr_code = Qrcode.query.get(qrcode_id)

    # If Qrcode is found, update the targetid
    if qr_code:
        qr_code.targetid = target_id
        db.session.commit()
    else:
        print(f"Qrcode with ID {qrcode_id} not found")


def update_qrcode_targetid_lock(qrcode_id, org_id):
    """
    This function updates the targetid of the Qrcode with the given qrcode_id
    to the specified target_id.
    """
    # Find the Qrcode by qrcode_id
    qr_code = Qrcode.query.get(qrcode_id)

    # If Qrcode is found, update the org_id
    if qr_code:
        qr_code.organization_id = org_id
        db.session.commit()
    else:
        print(f"Qrcode with ID {qrcode_id} not found")


if __name__ == "__main__":
    app.run(debug=True)
