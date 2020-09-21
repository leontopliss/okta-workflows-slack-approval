import json
import slack
import os

from secrets import get_secret
from logger import setup_logger

gcp_project_id = os.getenv('GCP_PROJECT')
slack_channel = get_secret(gcp_project_id, 'slack-channel')
slack_token = get_secret(gcp_project_id, 'slack-token')
log = setup_logger()

def approval_notify(request):

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

