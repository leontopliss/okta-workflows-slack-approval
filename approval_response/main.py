import json
import os

from secrets import get_secret
from logger import setup_logger

gcp_project_id = os.getenv('GCP_PROJECT')
slack_channel = get_secret(gcp_project_id, 'slack-channel')
slack_token = get_secret(gcp_project_id, 'slack-token')
log = setup_logger()

def approval_response(request):

    log.debug(request)
    print(request)

    return 'ok'