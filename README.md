# okta-workflows-slack-approval

A basic Slack approval capability for Okta workflows with Terraform deployment to GCP.

How this works at a high level:
1.  Where approval is required in an Okta workflow, the workflow calls the approval cloud function with context information
1. This approval notification function generates an ID, sends a message to Slack with Approve or Reject buttons and persists data in Firestore against the ID for later action
1. The user clicks approve or reject. This posts the response to a interactivity endpoint which then retrieves the previous context from Firestore and pushes all this info along with action to a separate Okta workflow to action.

Slack Message:

![Slack Message](/doc/images/slack_notification_1.png)

After Approval:

![Slack Message](/doc/images/slack_notification_2.png)

## Deploying to GCP using Terraform

1.  Create a project and attach billing
1.  Create a service account with Project Owner permissions. Download the key and place in this directory under creds.json
1.  Install docker (if you don't have it already) - https://www.docker.com/products/docker-desktop
1.  Deploy with Terraform
```
    docker run -v $(pwd):/app -w /app hashicorp/terraform:0.13.3 init
        
    docker run -v $(pwd):/app -w /app hashicorp/terraform:0.13.3 apply \
        --auto-approve \
        -var "project_id=your-project-id" \
        -var "region=europe-west2" \
        -var "credentials_file=creds.json"
```

## Configure Slack

1.  Go to https://api.slack.com/apps and create a new application
1. In the "OAuth & Permissions" menu add the scope chat:write
1. In the "OAuth & Permissions" click install to workspace. This will generate a "Bot User OAuth Access Token" which we will need to add to GCP secrets management
1. In the "Basic Information" menu take a note of the signing secret. We will need this for secrets management
1. In the "Interactivity & Shortcuts" menu, add the URL of the approval response cloud endpoint. This was returned by Terraform but can also be seen in the GCP console
1. Install the app to the channel you want to receive notifications too. The channel should be private to control access. Take a note of the channel ID (in the browser this is the last part of the URL when in the channel)


## Configure secrets in Google Secret Manager

Add your secrets to Google Secret Manager (These will be pre created by Terraform but will be empty):
* slack-token - take from the slack console as per instructions above
* slack-signing-secret - take from the slack console as per instructions above
* notification-key - A random key at least 10 characters in length we will use this in the requesting slack workflow
* workflows-callback-url - The url of the Okta Workflow the script will call on approval or rejection
* workflows-callback-token - The token to access the above URL

## Testing the approval notification function

You can test the approval outside of Workflows using curl by calling the approval notification endpoint using the key set in secrets management.

* type - is a field that is passed through to the callback workflow to determine the action required (could be a child flow)
* title - the title to appear on the Slack message
* slack_channel - specifies the channel the approval will be posted too
* msg_fields - determines the fields that will be displayed in the message (values taken from data)
* data - the context required to execute the workflow / action

```
curl -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "X-Api-Key: {your key}" \
-d 
'{
    "type": "new_user", 
    "title": "New User Request", 
    "slack_channel": "G013Y4AAAA",
    "msg_fields": ["firstName", "lastName", "manager", "email", "department"],
    "data": "{
        "firstName": "Martin",
        "lastName":"Brockson",
        "email": "martin.brokson@acme.com",
        "login": "martin.brokson@acme.com",
        "manager": "jim.smith@acme.com",
        "department": "Technology"
    }
}' https://{region}-{project}.cloudfunctions.net/approval_notification
```

After clicking approve or reject the following will be submitted to the callback workflow:

```
    {
        "type": "new_user",
        "data": {
            "requester": "jim.smith@acme.com",
            "lastName": "Brockson",
            "email": "martin.brokson@acme.com",
            "login": "martin.brokson@acme.com",
            "firstName": "Martin",
            "manager": "jim.smith@acme.com",
            "department": "Technology"
        },
        "requested_at": "2020-09-30T11:09:01.197000+00:00",
        "action": "approve"
    }
```

This data can then be actioned by the workflow

## Okta Workflows

Create:
1. requesting workflow
1. a callback workflow

### Requesting workflow

The first workflow needs to take the source data, construct it into a suitable format for the approval service and post it to the approval service. You can then take any other action required or just close the connection

![Slack Message](/doc/images/approval_request_workflow.png)

The requesting workflow could be triggered by any input. For example an API Endpoint if an external system is triggering the flow, a Google sheet etc..

### Callback Workflow

The second workflow must be triggered by as an API Endpoint. This takes the data submitted and performs any action required.

