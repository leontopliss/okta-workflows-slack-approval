import json
import os
import hmac
import hashlib
from time import time
import requests

from secrets import get_secret
from logger import setup_logger

gcp_project_id = os.getenv('GCP_PROJECT')
slack_signing_secret = None

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

        if msg_type == "block_actions" and action_id == "approve":
            log.debug('action approve')
            approve(json_data)
            return "action taken", 200
        elif msg_type == "block_actions" and action_id == "reject":
            log.debug('action reject')
            reject(json_data)
            return "action taken", 200

        return "no action taken", 200

    else:
        raise ValueError("Unknown content type: {}".format(content_type))


def verify_slack_signature(request):
    """Verify the request matches the slack signing secret"""
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

def json_response(url, msg):
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

def approve(data):
    response_text = ":tick: Approved by {}".format(data['user']['username'])
    response_msg = create_response_msg(response_text, data['message'])
    json_response(data['response_url'], response_msg)

def reject(data):
    response_text = ":x: Rejected by {}".format(data['user']['username'])
    response_msg = create_response_msg(response_text, data['message'])
    json_response(data['response_url'], response_msg)