import json
import os
from secrets import get_secret

gcp_project_id = os.getenv('GCP_PROJECT')
slack_channel = get_secret(gcp_project_id, 'slack-channel')
slack_token = get_secret(gcp_project_id, 'slack-token')


def approval_response(request):

    print(request)

    return 'ok'