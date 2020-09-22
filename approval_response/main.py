import json
import os
import hmac
import hashlib
from time import time

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
        action_name = json_data['actions'][0]['name'] 

        log.debug('type: {} action name: {}'.format(msg_type,action_name))

        if msg_type == "interactive_message" and action_name == "approve":
            log.debug('action approve')
            return approve(json_data), 200
        elif msg_type == "interactive_message" and action_name == "reject":
            log.debug('action reject')
            return reject(json_data), 200
            

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


def approve(data):
    user = data['user']['name']
    message = "Approved by {}".format(user)
    return message

def reject(data):
    user = data['user']['name']
    message = "Rejected by {}".format(user)
    return message