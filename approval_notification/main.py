import json
import slack
import os

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
    log.info('received approval request, title: {}, text {}'.format(title, text))

    client = slack.WebClient(token=slack_token)

    # Message posted to Slack as an attachment
    attachments = [
        {
            "mrkdwn_in": ["text"],
            "color": "#36a64f",
            "title": title,
            "text": text,
            "callback_id": "vsvsadsda",
            "actions": [
                {
                    "name": "approve",
                    "text": "Approve",
                    "type": "button",
                    "value": "value",
                    "style": "primary"
                },
                {
                    "name": "reject",
                    "text": "Reject",
                    "type": "button",
                    "value": "value",
                    "style": "danger",
                    "confirm": {
                        "title": "Are you sure?",
                        "text": "Are you sure?",
                        "ok_text": "Yes",
                        "dismiss_text": "No"
                    }
                }
            ]
        }
    ]

    # Send message to Slack
    client.chat_postMessage(
        channel=slack_channel,
        attachments=attachments
    )

    return 'ok'

