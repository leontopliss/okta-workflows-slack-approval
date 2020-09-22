import json
import slack
import os
import uuid

from secrets import get_secret
from logger import setup_logger

gcp_project_id = os.getenv('GCP_PROJECT')
slack_channel = None
slack_token = None
log = setup_logger()

def approval_notify(request):

    # loading secrets as lazy globals
    # can't be global as this creates issues with automated deployment
    # as cold start on initial deployment can't access the variables
    global slack_channel, slack_token

    if not slack_channel:
        slack_channel = get_secret(gcp_project_id, 'slack-channel')

    if not slack_token:
        slack_token = get_secret(gcp_project_id, 'slack-token')

    title = 'Test Approval'
    text = 'Access to iBusiness'
    callback_id = uuid.uuid4().hex
    log.info('received approval request, title: {}, text {}'.format(title, text))

    client = slack.WebClient(token=slack_token)

    # Message posted to Slack as blocks
    new_user_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "New User Request\n"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Name*\nJohn Smith"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Manager:*\nmartin.knowes@itv.com"
                },
                {
                    "type": "mrkdwn",
                    "text": "*User email*\njohn.smith@itv.com"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Department:*\nTechnology"
                }
            ]
        },
        {
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
                    "value": "click_me_123"
                },
                {
                    "type": "button",
                    "action_id": "reject",
                    "text": {
                        "type": "plain_text",
                        "text": "Reject"
                    },
                    "style": "danger",
                    "value": "click_me_123"
                }
            ]
        }
    ]

    # Send message to Slack
    client.chat_postMessage(
        channel=slack_channel,
        blocks=new_user_blocks
    )

    return 'ok'

