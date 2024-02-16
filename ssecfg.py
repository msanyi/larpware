# ssecfg.py
from flask import Response, request, jsonify, Blueprint, stream_with_context
from sqlalchemy.orm.exc import StaleDataError
from database import db, NodeOperationsHistory, NodeUsers, Node, MetUsers, EventQueue, SSEClient
from datetime import datetime
import json
import time
import traceback


SSE_CONFIG = {
    'user_operations_check_interval': 5,  # from 1 to 5 seconds
    'node_status_check_interval': 10,     # from 5 to 10 seconds
}


sse_blueprint = Blueprint('sse', __name__)


class ClientManager:
    def __init__(self):
        self.clients_dict = {}

    def add_client(self, user_id, client, node_id=None):
        # new in-db solution
        self.clear_messages(user_id)
        client = SSEClient(user_id=user_id, last_event=time.time())
        db.session.merge(client)
        db.session.commit()

    def delayed_remove_client(self, user_id, delay=5):  # 5 seconds delay by default
        print(f"[DEBUG] DELAYED Removing client with user_id: {user_id} in 5 secs if timestamp does not get an update.")

        def task():
            # print(f"[DEBUG] Starting delayed removal task for user {user_id} with delay {delay}")
            time.sleep(delay)
            client = self.get_client(user_id)
            if client is None:  # If the client doesn't exist
                print("no client_data: ", user_id)
                return
            # Check if the timestamp has changed, indicating a reconnection
            if client.last_event <= time.time() - delay:
                # current_ts = time.time()
                # client_ts = client.last_event
                # print(f"[DEBUG] Current timestamp: {current_ts}, Client timestamp: {client_ts}, Delay: {delay}")
                self.remove_client(user_id)

        # This will work with gevent because it internally patches the threading module
        # but be aware that this is still cooperative multitasking and not preemption-based
        time.sleep(delay)
        task()

    def remove_client(self, user_id):
        # new in-db solution
        SSEClient.query.filter(SSEClient.user_id == user_id).delete()
        db.session.commit()
        self.clear_messages(user_id)
        print("removed client", user_id)

    def get_client(self, user_id):
        return SSEClient.query.filter(SSEClient.user_id == user_id).first()

    def send_message(self, user_id, data_str):
        # new in-db solution
        client = SSEClient.query.filter(SSEClient.user_id == user_id).first()
        if client is not None:
            db.session.add(EventQueue(user_id=user_id, data=data_str))
            db.session.commit()
        else:
            print(f"[ERROR] Failed to send message to user {user_id} as the client does not exist.")

    def pop_message(self, user_id):
        event = EventQueue.query.filter(EventQueue.user_id == user_id).first()
        if event is None:
            # print ("no messages for user")
            return None
        else:
            responsedata = event.data
            db.session.delete(event)
            db.session.commit()
            # print ("popped", responsedata)
            return responsedata
    
    def clear_messages(self, user_id):
        EventQueue.query.filter_by(user_id=user_id).delete()

    def update_timestamp(self, user_id, timestamp):
        # in-db solution
        client_db_data = self.get_client(user_id)
        if client_db_data is not None:
            client_db_data.last_event = timestamp
            try:
                db.session.commit()
            except StaleDataError as e:
                db.session.rollback()
                print("Suppressed error: encountered StaleDataError when trying to update SSE timestamp for user", user_id)
            # print(f"[DEBUG] Updated db timestamp for user {user_id}, set to {client_db_data.last_event}")


client_manager = ClientManager()


# The sse_push function to send updates to all connected clients
def sse_push(user_id, event, data):
    # print(f"[DEBUG] Pushing SSE message to user {user_id} with event {event} and data {data}.")
    data_str = json.dumps({"event": event, "data": data})
    client_manager.send_message(user_id, data_str)


@sse_blueprint.route('/acknowledge', methods=['POST'])
def acknowledge():
    data = request.json
    user_id = data.get('user_id')
    timestamp = time.time()

    if user_id and timestamp:
        client_manager.update_timestamp(user_id, timestamp)
        return jsonify(status="success"), 200
    else:
        return jsonify(status="error", message="Invalid data"), 400


@sse_blueprint.route('/sse')
def sse_endpoint():
    user_id = request.args.get('user_id')

    # Check if user_id exists and is valid
    if not user_id or not user_id.isdigit():
        print("invalid user: ", user_id)
        return "Invalid user_id", 400

    user_id = int(user_id)
    client_manager.add_client(user_id, request.environ['wsgi.input'])
    # print(f"[DEBUG] SSE connection established for user {user_id}. Client added to ClientManager.")

    # The event stream function.
    @stream_with_context
    def generate_event_stream():
        # print("-------------------------- SSE generate_event_stream path")
        yield f"data: {json.dumps({'message': 'connection established'})}\n\n"
        
        while True:
            try:
                # Check if client manager has SSE messages queued
                # If yes, send it. If no, send a keepalive
                client = client_manager.get_client(user_id)

                if client is None:
                    print(f"[DEBUG] Client {user_id} not found in client_manager, exiting generator")
                    break

                last_timestamp = client.last_event  
                newMessage = client_manager.pop_message(user_id)
                current_time = time.time()
                # print ("last_event is--:", client.last_event)
                # print ("current_time is:", current_time)

                if newMessage is not None:
                    print(user_id, "received message", newMessage)

                if newMessage is not None:
                    # print(f"[DEBUG] Yielding data from event_queue for user {user_id}")
                    client_manager.update_timestamp(user_id, current_time)
                    yield f"data: {newMessage}\n\n"
                else:
                    # print(f"[DEBUG] Yielding keep-alive for user {user_id}")
                    if current_time - last_timestamp < 5:
                        # print(f"[DEBUG] Sleeping for user {user_id}")
                        time.sleep(1)
                        continue
                    else:
                        client_manager.update_timestamp(user_id, current_time)
                        yield f"data: {json.dumps({'message': 'keep-alive'})}\n\n"
            except GeneratorExit:
                # Client has closed the connection
                print(f"[DEBUG] SSE connection closed by user {user_id}. Removing client from ClientManager.")
                client_manager.delayed_remove_client(user_id)
                break
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[ERROR] {current_time} - An error occurred: {e}")
                traceback.print_exc()  # This prints the stack trace
                break

    response = Response(generate_event_stream(), mimetype="text/event-stream")
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'

    return response

