import json
import slack
import os
import uuid
from google.cloud import firestore

from secrets import get_secret
from logger import setup_logger

gcp_project_id = os.getenv('GCP_PROJECT')
slack_token = None
notification_key  = None

log = setup_logger()

def approval_notify(request):

    # loading secrets as lazy globals
    # can't be global as this creates issues with automated deployment
    # as cold start on initial deployment can't access the variables
    global slack_channel, slack_token, notification_key

    if not notification_key:
        notification_key = get_secret(gcp_project_id, 'notification-key')

    if ('X-Api-Key' not in request.headers or not api_key_valid(request.headers['X-Api-Key'])):
        log.fatal('API key is invalid')
        return 'unauthorized', 403

    if not api_key_long_enough(request.headers['X-Api-Key']):
        log.warning('API key is too short please make it at least 10 characters')

    try:
        request_json = request.get_json(silent=True)
        title = request_json["title"]
        approval_type = request_json["type"]
        data = json.loads(request_json["data"])
        msg_fields = request_json["msg_fields"]
        slack_channel = request_json["slack_channel"]
    except KeyError as err:
        log.error('payload malformed or mandatory data missing: {}'.format(err))
        return 'payload malformed or mandatory data missing', 500

    log.debug(json.dumps(request_json))
    
    request_id = uuid.uuid4().hex

    if not slack_token:
        slack_token = get_secret(gcp_project_id, 'slack-token')

    client = slack.WebClient(token=slack_token)    

    # Message posted to Slack as blocks
    msg_blocks = [
        construct_title_msg_blocks(title),
        construct_field_msg_blocks(msg_fields,data),
        construct_actions_msg_block(request_id)
    ]

    write_to_datastore(request_id, approval_type, data)

    # Send message to Slack
    try:
        client.chat_postMessage(
            channel=slack_channel,
            blocks=msg_blocks
        )
    except slack.errors.SlackApiError as err:
        log.error('could not post to slack: {}'.format(err))
        return 'error posting to slack', 500

    return 'ok', 200


def api_key_valid(key_provided):
    if (key_provided == notification_key):
        return True
    else:
        return False

def api_key_long_enough(key_provided):
    if len(key_provided) < 10:
        return False
    else:
        return True

def construct_title_msg_blocks(title):
    title_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "{}\n".format(title)
        }
    }
    return title_block


def construct_field_msg_blocks(msg_fields, data):
    msg_fields_list = []
    for field in msg_fields:
        try:
            field_data = data[field]
        except KeyError:
            log.debug('could not find field {} in the data'.format(field))
            continue
        
        #TODO temporarily displaying fields as lower case
        # add in display name
        json_field = {
            "type": "mrkdwn",
            "text": "*{}*\n{}".format(field.lower(),field_data) 
        }

        msg_fields_list.append(json_field)

    field_block = {
        "type": "section",
        "fields": msg_fields_list
    }

    return field_block

def construct_actions_msg_block(request_id):
    actions_block = {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "action_id": "approve",
                "text": {
                    "type": "plain_text",
                    "text": "Approve"
                },
                "style": "primary",
                "value": request_id
            },
            {
                "type": "button",
                "action_id": "reject",
                "text": {
                    "type": "plain_text",
                    "text": "Reject"
                },
                "style": "danger",
                "value": request_id
            }
        ]
    }

    return actions_block


def write_to_datastore(request_id, approval_type, data):

    db = firestore.Client()
    doc_ref = db.collection('approvals').document(request_id)
    doc_ref.set({
        'type': approval_type,
        'status': 'approval_required',
        'requested_at': firestore.SERVER_TIMESTAMP,
        'data': data
    })
