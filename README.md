# okta-workflows-slack-approval
 Slack approvals using Okta Workflows


## Deploying to GCP using Terraform

docker run -v $(pwd):/app -w /app hashicorp/terraform:0.13.3 init

docker run -v $(pwd):/app -w /app hashicorp/terraform:0.13.3 apply \
    --auto-approve \
    -var "project_id=slack-approval-lab" \
    -var "region=europe-west2" \
    -var "credentials_file=creds.json"



## Using the approval notification function

curl -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "X-Api-Key: {your key}" \
-d 
'{
    "type": "new_user", 
    "title": "New User Request", 
    "slack_channel": "G013Y4BRUBU",
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