from flask import Blueprint, jsonify, render_template, session, request
from database import User, Userenvelope, Envelope, db
from navbar import NavBarInfo

envelopes_app = Blueprint('envelopes_app', __name__)

def getEnvelopeCount():
    user_id = session.get('user_id')
    if not user_id:
        return 0

    user = User.query.get(user_id)
    if not user:
        return 0
    
    user_envelopes = Userenvelope.query.filter_by(user_id=user_id).all()
    return len(user_envelopes)

def getUnopenedEnvelopeCount():
    user_id = session.get('user_id')
    if not user_id:
        return 0

    user = User.query.get(user_id)
    if not user:
        return 0
    
    user_envelopes = Userenvelope.query.filter_by(user_id=user_id).filter_by(opened=False).all()
    return len(user_envelopes)


@envelopes_app.route('/envelopes', methods=['GET'])
def envelopes_page():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Querying all user envelopes
    user_envelopes = Userenvelope.query.filter_by(user_id=user_id).all()

    # Preparing the data to be displayed in the template
    envelopes_data = [{
        "id": ue.envelope_id,
        "number": ue.envelope.number,
        "opening_condition": ue.envelope.opening_condition,
        "opened": ue.opened,
        "content": ue.envelope.content if ue.opened else None
    } for ue in user_envelopes]
    print("Debug: Envelopes Data:", envelopes_data)

    return render_template('envelopes.html', envelopes=envelopes_data, headerinfo=NavBarInfo())


@envelopes_app.route('/envelopes/open/<int:envelope_id>', methods=['POST'])
def open_envelope(envelope_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_envelope = Userenvelope.query.filter_by(user_id=user_id, envelope_id=envelope_id).first()
    if not user_envelope:
        return jsonify({"error": "Envelope not found for this user"}), 404

    # Here you can perform any checks based on opening_condition and decide whether to allow opening the envelope
    # If opening is allowed, set the 'opened' attribute to True
    user_envelope.opened = True
    db.session.commit()

    return jsonify({"success": "Envelope opened successfully", "content": user_envelope.envelope.content})
