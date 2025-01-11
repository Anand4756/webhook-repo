from datetime import datetime, timezone
import uuid
from flask import Blueprint, request, jsonify, render_template
from app.extensions import mongo

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

def create_action_data(action_type, author, request_id, from_branch, to_branch, timestamp):
    """Creates a structured action data dictionary."""
    return {
        "_id": uuid.uuid4().hex,
        "request_id": request_id,
        "author": author,
        "action": action_type,
        "from_branch": from_branch,
        "to_branch": to_branch,
        "timestamp": timestamp,
    }

def extract_push_action(data):
    """Extracts action data for push events."""
    author = data["pusher"]["name"]
    to_branch = data["ref"].split("/")[-1]
    timestamp = datetime.now(timezone.utc).isoformat()
    return create_action_data("PUSH", author, data["after"], None, to_branch, timestamp)

def extract_pull_request_action(data):
    """Extracts action data for pull request events."""
    pr = data["pull_request"]
    author = pr["user"]["login"]
    from_branch = pr["head"]["ref"]
    to_branch = pr["base"]["ref"]
    timestamp = pr["updated_at"]
    return create_action_data("PULL_REQUEST", author, pr["id"], from_branch, to_branch, timestamp)

def extract_merge_action(data):
    """Extracts action data for merge events."""
    author = data["pull_request"]["merged_by"]['login']
    from_branch = data['pull_request']['head']['label'].split(':')[-1],
    to_branch = data['pull_request']['base']['label'].split(':')[-1],
    timestamp = datetime.now(timezone.utc).isoformat()
    return create_action_data("MERGE", author, data['pull_request']['id'], from_branch, to_branch, timestamp)

@webhook.route('/')
def index():
    return render_template('index.html')

@webhook.route("/webhook", methods=["POST"])
def webhook_receive():
    try:
        collection = mongo.db.actions
        print("Received webhook request")
        data = request.json

        # Determine the action type and extract corresponding action data
        if "pusher" in data:
            action_data = extract_push_action(data)
        elif "pull_request" in data:
            if data["pull_request"].get("merged_by") is not None:
                # Handle merge action
                action_data = extract_merge_action(data)
            else:
                # Handle regular pull request action
                action_data = extract_pull_request_action(data)
        else:
            return jsonify({"error": "Unhandled event type"}), 400

        # Store the action data in MongoDB
        collection.insert_one(action_data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500

@webhook.route("/actions", methods=["GET"])
def get_actions():
    """Fetches the most recent actions from MongoDB."""
    try:
        collection = mongo.db.actions
        actions = list(collection.find().sort("timestamp", -1).limit(10))
        for action in actions:
            action["_id"] = str(action["_id"])
        return jsonify(actions)
    except Exception as e:
        print(f"Error fetching actions: {str(e)}")
        return jsonify({"error": str(e)}), 500
