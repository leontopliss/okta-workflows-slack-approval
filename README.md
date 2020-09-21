# okta-workflows-slack-approval
 Slack approvals using Okta Workflows


docker run -v $(pwd):/app -w /app hashicorp/terraform:0.13.3 init

docker run -v $(pwd):/app -w /app hashicorp/terraform:0.13.3 apply \
    --auto-approve \
    -var "project_id=slack-approval-lab" \
    -var "region=europe-west2" \
    -var "credentials_file=creds.json"