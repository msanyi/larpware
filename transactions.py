# this is the beginning of transactions.py
from flask import Blueprint, jsonify, request  # Import the necessary modules from Flask
from database import db, User, Transaction, Messages  # Import the 'db', 'User', 'Transaction', and 'Messages' models from the 'database' module
from flask import session

transactions = Blueprint('transactions', __name__)  # Create a blueprint named 'transactions'


@transactions.route('/transaction', methods=['POST'])
def make_transaction(sender_id=None, receiver_id=None, amount=None):
    # Extract the data from the request's JSON payload
    data = request.json
    sender_id = data.get('senderId')
    receiver_id = data.get('receiverId')
    amount = int(data.get('amount', 0))  # Convert to float once
    print("Received Data:", request.data)

    if not sender_id or not receiver_id or amount <= 0:
        print("valami none... kilép")
        return jsonify({'error': 'Invalid transaction data'}), 400

    if amount <= 0:  # Ensure the amount is not zero or negative
        return jsonify({'error': 'Clever, but try to send a positive amount next time.'}), 400
    sender = User.query.get_or_404(sender_id)
    receiver = User.query.get_or_404(receiver_id)

    if sender.balance < amount:
        return jsonify({'error': 'Insufficient balance'}), 403

    print(f"user balance before transaction, old balance: {sender.balance}")
    session['balance'] = sender.balance
    sender.balance -= amount
    receiver.balance += amount

    print(f"user balance after transaction, new balance: {sender.balance}")

    # Update the session balance if the sender is the current session user
    if sender_id == session.get('user_id'):
        session['balance'] = sender.balance

    transaction = Transaction(sender_id=sender_id, receiver_id=receiver_id, amount=amount)
    db.session.add(transaction)

    message_content = f"{sender.username} sent {receiver.username} {amount} €$"
    new_message = Messages(sender_id=sender.id, receiver_id=receiver.id, messagecontent=message_content, is_system=True)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({'message': 'Transaction successful!', 'class': 'cyberpunk-success', 'new_balance': sender.balance}), 200


@transactions.route('/balance/<int:user_id>', methods=['GET'])  # Decorator to specify the URL route and HTTP method for the following function
def check_balance(user_id):
    user = User.query.get(user_id)  # Retrieve the User object with the given 'user_id'
    if not user:  # Check if the user doesn't exist
        return jsonify({'error': 'User not found'}), 404  # Return a JSON response with an error message and status code 404 (Not Found)
    return jsonify({'balance': user.balance}), 200  # Return a JSON response with the user's balance and status code 200 (OK)


@transactions.route('/history/<int:user_id>', methods=['GET'])  # Decorator to specify the URL route and HTTP method for the following function
def transaction_history(user_id):
    # Retrieve the User object with the given 'user_id'
    user = User.query.get(user_id)
    # Check if the user doesn't exist
    if not user:
        # Return a JSON response with an error message and status code 404 (Not Found)
        return jsonify({'error': 'User not found'}), 404
    # Query the Transaction table to find all transactions involving the given 'user_id' as the sender or receiver
    user_transactions = Transaction.query.filter((Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)).all()
    # Create an empty list to store transaction details
    transaction_list = []
    # Iterate over each transaction
    for transaction in user_transactions:
        # Add the transaction details to the list
        transaction_list.append({
            'transaction_id': transaction.id,
            'sender_id': transaction.sender_id,
            'receiver_id': transaction.receiver_id,
            'amount': transaction.amount
        })
    # Return a JSON response containing the list of transaction details with status code 200 (OK)
    return jsonify(transaction_list), 200

# this is the end of transactions.py
