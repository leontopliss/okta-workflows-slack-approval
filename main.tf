terraform {
  required_version = ">= 0.13.0"
}

variable "project_id" {}
variable "region" {}
variable "credentials_file" {}

variable "max_time_to_meaningful_paint" {
  default = 3000
}
variable "local_output_path" {
  default = "build"
}

provider "google" {
  credentials = file("${var.credentials_file}")
  project = var.project_id
  region = var.region
  user_project_override = true
}

provider "archive" {}

resource "google_project_service" "services" {
  project = var.project_id
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudfunctions.googleapis.com"
  ])
  service            = each.value
  disable_on_destroy = false
}

// Create Secrets
resource "google_secret_manager_secret" "setup" {

  for_each = toset([
    "slack-token",
    "slack-channel",
  ])

  secret_id = each.value

  replication {
    automatic = true
  }

  depends_on = [google_project_service.services]
}

// Create a bucket
resource "google_storage_bucket" "bucket_source_archives" {
  name = "${var.project_id}-gcf-source-archives"
  storage_class = "REGIONAL"
  location  = var.region
  force_destroy = "true"
  depends_on = [
    google_project_service.services
  ]
}

/**
 * Cloud Functions.
 * For each function, zip up the source and upload to GCS.
 * Uploaded source is referenced in the Function deploy.
 */

data "archive_file" "local_approval_notification_source" {
  type        = "zip"
  source_dir  = "./approval_notification"
  output_path = "${var.local_output_path}/approval_notification.zip"
}

// Add hash to filename to make cloud functions notice that the source has changed and deploy a new version
resource "google_storage_bucket_object" "gcs_approval_notification_source" {
  name   = format("approval_notification#%s.zip", data.archive_file.local_approval_notification_source.output_md5)
  bucket = google_storage_bucket.bucket_source_archives.name
  source = data.archive_file.local_approval_notification_source.output_path
}

resource "google_cloudfunctions_function" "function_approval_notification" {
  name = "approval_notification"
  description = "Approvals submitted to this function"
  available_memory_mb = 256
  project = var.project_id
  region = var.region
  timeout               = 60
  entry_point           = "approval_notify"
  trigger_http          = true
  runtime               = "python37"
  source_archive_bucket = google_storage_bucket.bucket_source_archives.name
  source_archive_object = google_storage_bucket_object.gcs_approval_notification_source.name

  depends_on = [
    google_project_service.services
  ]
}

// Make the cloud function public
resource "google_cloudfunctions_function_iam_binding" "binding_approval_notification" {
  project = var.project_id
  region = var.region
  cloud_function = google_cloudfunctions_function.function_approval_notification.name
  role = "roles/cloudfunctions.invoker"
  members = [
    "allUsers",
  ]
}

// All the cloud function access to secrets
resource "google_secret_manager_secret_iam_member" "approval_notification_secrets_iam" {

  for_each = toset([
    "slack-token",
    "slack-channel",
  ])

  project = var.project_id
  secret_id = each.value
  role = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_cloudfunctions_function.function_approval_notification.service_account_email}"

  depends_on = [
    google_secret_manager_secret.setup
  ]
}

// Approval response function
data "archive_file" "local_approval_response_source" {
  type        = "zip"
  source_dir  = "./approval_response"
  output_path = "${var.local_output_path}/approval_response.zip"
}

// Add hash to filename to make cloud functions notice that the source has changed and deploy a new version
resource "google_storage_bucket_object" "gcs_approval_response_source" {
  name   = format("approval_response#%s.zip", data.archive_file.local_approval_response_source.output_md5)
  bucket = google_storage_bucket.bucket_source_archives.name
  source = data.archive_file.local_approval_response_source.output_path
}

// Make the cloud function public
resource "google_cloudfunctions_function" "function_approval_response" {
  name = "approval_response"
  description = "Approvals response submitted to this function"
  available_memory_mb = 256
  project = var.project_id
  region = var.region
  timeout               = 60
  entry_point           = "approval_response"
  trigger_http          = true
  runtime               = "python37"
  source_archive_bucket = google_storage_bucket.bucket_source_archives.name
  source_archive_object = google_storage_bucket_object.gcs_approval_response_source.name

  depends_on = [
    google_project_service.services
  ]
}

resource "google_cloudfunctions_function_iam_binding" "binding_approval_response" {
  project = var.project_id
  region = var.region
  cloud_function = google_cloudfunctions_function.function_approval_response.name
  role = "roles/cloudfunctions.invoker"
  members = [
    "allUsers",
  ]
}


// define output variables for use downstream
output "project" {
  value = var.project_id
}
output "region" {
  value = var.region
}

output "function_approval_notification_name" {
  value = "${google_cloudfunctions_function.function_approval_notification.name}"
}

output "function_approval_notification_endpoint" {
  value = "${google_cloudfunctions_function.function_approval_notification.https_trigger_url}"
}

output "function_approval_response" {
  value = "${google_cloudfunctions_function.function_approval_response.name}"
}

output "function_approval_response_endpoint" {
  value = "${google_cloudfunctions_function.function_approval_response.https_trigger_url}"
}