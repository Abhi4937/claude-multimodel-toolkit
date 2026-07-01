"""
Cloud Function (Gen2) — hard billing kill-switch.

Triggered by a Cloud Billing Budget via Pub/Sub. When the reported cost exceeds
the budget amount, it DISABLES BILLING on the target project — a true hard stop
(all billable services halt). This is the only way to guarantee a spend ceiling
on a paid GCP account (budget alerts alone only email you).

Deploy: see DEPLOY.md in this folder.
Entry point: stop_billing
Env var required: GCP_PROJECT_TO_DISABLE = <the project id to protect>
"""
import base64
import json
import os

import functions_framework
from googleapiclient import discovery

PROJECT_ID = os.environ.get("GCP_PROJECT_TO_DISABLE", "")
PROJECT_NAME = f"projects/{PROJECT_ID}"


@functions_framework.cloud_event
def stop_billing(cloud_event):
    # Budget notification arrives as a Pub/Sub message wrapped in a CloudEvent.
    msg = cloud_event.data["message"]
    payload = base64.b64decode(msg["data"]).decode("utf-8")
    info = json.loads(payload)

    cost = float(info.get("costAmount", 0))
    budget = float(info.get("budgetAmount", 0))
    print(f"budget='{info.get('budgetDisplayName')}' cost={cost} budget={budget}")

    if not PROJECT_ID:
        print("ERROR: GCP_PROJECT_TO_DISABLE env var not set — cannot act.")
        return

    if cost <= budget:
        print(f"No action: cost {cost} <= budget {budget}")
        return

    billing = discovery.build("cloudbilling", "v1", cache_discovery=False)
    projects = billing.projects()

    if _is_billing_enabled(PROJECT_NAME, projects):
        _disable_billing(PROJECT_NAME, projects)
    else:
        print("Billing already disabled — nothing to do.")


def _is_billing_enabled(project_name, projects):
    try:
        res = projects.getBillingInfo(name=project_name).execute()
        return bool(res.get("billingEnabled", False))
    except Exception as e:  # noqa: BLE001
        print(f"Could not read billing status: {e}")
        return False


def _disable_billing(project_name, projects):
    body = {"billingAccountName": ""}  # empty = detach billing = HARD STOP
    projects.updateBillingInfo(name=project_name, body=body).execute()
    print(f"!!! BILLING DISABLED on {project_name} — spend ceiling hit.")
