## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
from better_profanity import profanity

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!' # change to something random, no matter what

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://vm146.rz.uni-osnabrueck.de/hub'
HUB_AUTHKEY = '12Crr-K24d-2N'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "THE Creative Insults"
CHANNEL_ENDPOINT = "http://vm146.rz.uni-osnabrueck.de/u008/task_3/channel.wsgi" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:chat'

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
                                "name": CHANNEL_NAME,
                                "endpoint": CHANNEL_ENDPOINT,
                                "authkey": CHANNEL_AUTHKEY,
                                "type_of_service": CHANNEL_TYPE_OF_SERVICE,
                             }))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        print(response.text)
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # Check authorization and message presence (existing code)
    if not check_authorization(request):
        return "Invalid authorization", 400
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    if not 'extra' in message:
        extra = None
    else:
        extra = message['extra']

    # Profanity check
    if contains_profanity(message['content']):
        # Censor the profanity in the original message
        censored_content = censor_profanity(message['content'])

        # Create a response message
        response_message = {
            "sender": "Ah! Boring Insult detected",
            "content": f"Can't you do better than: {censored_content}?",
            "timestamp": message['timestamp'],  # Use the same timestamp
            "extra": extra
        }

        #add the original message to the content list
        message['content'] = censored_content
        messages.append(message)
        messages = limit_messages(messages)
        save_messages(messages)

        # Add the response message to the messages list
        messages = read_messages()
        messages.append(response_message)
        messages = limit_messages(messages)
        save_messages(messages)

        return "Profanity detected and censored", 200

    # If no profanity, add the original message
    messages = read_messages()
    messages.append({
        'content': message['content'],
        'sender': message['sender'],
        'timestamp': message['timestamp'],
        'extra': extra,
    })
    messages = limit_messages(messages)
    save_messages(messages)
    return "OK", 200

def censor_profanity(text):
    """Censor profanity in the text using better_profanity."""
    return profanity.censor(text)

def contains_profanity(text):
    """Check if the text contains profanity using better_profanity."""
    return profanity.contains_profanity(text)


def read_messages():
    global CHANNEL_FILE
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def limit_messages(messages):
    # Check if the number of messages exceeds the limit
    if len(messages) > 11:
        # Remove the second oldest message (index 1, since index 0 is the oldest)
        messages.pop(1)
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

# Start development web server
# run flask --app channel.py register
# to register channel with hub

if __name__ == '__main__':
    app.run(port=5001, debug=True)
