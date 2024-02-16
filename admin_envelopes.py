from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from database import Envelope, Userenvelope, User
from database import db

admin_envelopes_app = Blueprint('admin_envelopes', __name__)


@admin_envelopes_app.route('/envelopes', methods=['GET'])
def envelopes():
    envelopes = Envelope.query.all()
    users = User.query.filter(~User.username.contains(['Architecture Watchdog'])).order_by(User.username).all()
    userenvelopes = Userenvelope.query.all()

    envelopes_data = []
    for envelope in envelopes:
        envdata = {}
        envdata['id']=envelope.id
        envdata['number']=envelope.number
        envdata['opening_condition']=envelope.opening_condition
        envdata['content']=envelope.content
        envdata['users']=[]
        userenvelopes = Userenvelope.query.filter(Userenvelope.envelope_id==envelope.id).all()
        for ue in userenvelopes:
            user = User.query.get(ue.user_id)
            uedata = {
                'id':user.id,
                'username':user.username,
                'isopen':ue.opened
            }
            envdata['users'].append(uedata)
        envelopes_data.append(envdata)


    return render_template('admin_envelopes.html', envelopes=envelopes_data, users=users)

@admin_envelopes_app.route('/envelopes/create', methods=['POST'])
def create_envelope():
    condition = request.json.get('condition')
    content = request.json.get('content')
    max_num = db.session.query(db.func.max(Envelope.number)).scalar() or 0
    envelope_num = max_num + 1
    envelope = Envelope(
        number=envelope_num,
        opening_condition=condition,
        content=content
    )
    db.session.add(envelope)
    db.session.commit() 
    return jsonify({"success":"true"}), 200

@admin_envelopes_app.route('/envelopes/delete/<int:envelope_id>', methods=['POST'])
def delete_envelope(envelope_id):
    Userenvelope.query.filter(Userenvelope.envelope_id == envelope_id).delete()
    db.session.commit()
    Envelope.query.filter(Envelope.id == envelope_id).delete()
    db.session.commit()
    return jsonify({"success":"true"}), 200

@admin_envelopes_app.route('/envelopes/update/<int:envelope_id>', methods=['POST'])
def modify_envelope(envelope_id):
    condition = request.json.get('condition')
    content = request.json.get('content')
    envelope = Envelope.query.filter(Envelope.id == envelope_id).first()
    if envelope is None:
        return jsonify({"error":"envelope not found"}), 400
    
    envelope.opening_condition = condition
    envelope.content = content
    db.session.commit()
    return jsonify({"success":"true"}), 200

@admin_envelopes_app.route('/envelopes/assign/<int:envelope_id>', methods=['POST'])
def assign_user_to_envelope(envelope_id):
    userId = int(request.json.get('user'))
    old = Userenvelope.query.filter(Userenvelope.envelope_id == envelope_id, Userenvelope.user_id == userId).first()
    if old is not None:
        return jsonify({"error": "assignment already exists"}), 400
    
    newUe = Userenvelope(envelope_id=envelope_id, user_id=userId)
    db.session.add(newUe)
    db.session.commit()

    return jsonify({"success":"true"}), 200

@admin_envelopes_app.route('/envelopes/deassign/<int:envelope_id>', methods=['POST'])
def deassign_user_from_envelope(envelope_id):
    userId = int(request.json.get('user'))
    Userenvelope.query.filter(Userenvelope.envelope_id == envelope_id, Userenvelope.user_id == userId).delete()
    db.session.commit()
    return jsonify({"success":"true"}), 200
