import json
import os
import hmac
import hashlib
from time import time
import requests
from google.cloud import firestore

from secrets import get_secret
from logger import setup_logger

gcp_project_id = os.getenv('GCP_PROJECT')
slack_signing_secret = None
workflows_callback_url = None
workflows_callback_token = None

log = setup_logger()

def approval_response(request):

    # loading secrets as lazy globals
    # can't be global as this creates issues with automated deployment
    # as cold start on initial deployment can't access the variables
    global slack_signing_secret

    if not slack_signing_secret:
        slack_signing_secret = get_secret(gcp_project_id, 'slack-signing-secret')

    content_type = request.headers['content-type']
    if content_type == 'application/x-www-form-urlencoded':

        if not verify_slack_signature(request):
            raise ValueError("slack response signature invalid")

        # Slack Guide:
        # Your Action URL will receive a HTTP POST request, including a payload 
        # body parameter, itself containing an application/x-www-form-urlencoded 
        # JSON string.
        json_data = json.loads(request.form["payload"])
        log.debug(json_data)

        msg_type = json_data['type']
        action_id = json_data['actions'][0]['action_id'] 

        if msg_type == "block_actions":
            block_action_process(json_data, action_id)
            return "action taken", 200

        return "no action taken", 500

    else:
        raise ValueError("Unknown content type: {}".format(content_type))


def verify_slack_signature(request):
    signature = request.headers.get("X-Slack-Signature")
    req_timestamp = request.headers.get("X-Slack-Request-Timestamp")
    req_body = request.get_data().decode("utf-8")

    if not signature:
        log.error("X-Slack-Signature header missing")
        return False
    if not req_timestamp:
        log.error("X-Slack-Request-Timestamp header missing")
        return False
    if abs(time() - int(req_timestamp)) > 60 * 5:
        log.error("X-Slack-Request-Timestamp too old")
        return False

    req_string = str.encode('v0:' + req_timestamp + ':' + req_body)
    req_hash = 'v0=' + hmac.new(str.encode(slack_signing_secret),
                                    req_string,
                                    hashlib.sha256).hexdigest()

    if hmac.compare_digest(req_hash, signature):
        return True
    else:
        log.error("signature digest does not match")
        return False

def create_response_msg(response_text, original_msg):
    feedback = {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": response_text
            }
        ]
    }

    response_msg = {
        "blocks": [original_msg['blocks'][0], original_msg['blocks'][1], feedback],
        "replace_original": True
    }

    log.debug(response_msg)

    return response_msg

def slack_response(url, msg):
    response = requests.post(
        url, 
        json=msg, 
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )

def block_action_process(data, action_id):

    if action_id == 'approve':
        response_text = ":tick: Approved by {}".format(data['user']['username'])
    elif action_id == 'reject':
        response_text = ":x: Rejected by {}".format(data['user']['username'])

    db_record = read_from_datastore(data['actions'][0]['value'])
    db_record['action'] = action_id
    okta_workflows_callback(db_record)

    response_msg = create_response_msg(response_text, data['message'])
    slack_response(data['response_url'], response_msg)

def read_from_datastore(request_id):
    db = firestore.Client()
    doc_ref = db.collection('approvals').document(request_id)
    doc = doc_ref.get()

    if doc.exists:
        db_data = doc.to_dict()
        #convert datetime object to string
        if 'requested_at' in db_data:
            db_data['requested_at'] = db_data['requested_at'].isoformat()
        #remove status. we are changing status now so it's not accurate
        if 'status' in db_data:
            del db_data['status']
        
        return db_data
    else:
        raise ValueError('no record for approval id: {}'.format(request_id))


def okta_workflows_callback(data):
    global workflows_callback_url, workflows_callback_token

    if not workflows_callback_url:
        workflows_callback_url = get_secret(gcp_project_id, 'workflows-callback-url')

    if not workflows_callback_token:
        workflows_callback_token = get_secret(gcp_project_id, 'workflows-callback-token')

    response = requests.post(
        workflows_callback_url, 
        json=data, 
        headers={
            'x-api-client-token': workflows_callback_token,
            'Content-Type': 'application/json'
        }
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to okta workflows returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )