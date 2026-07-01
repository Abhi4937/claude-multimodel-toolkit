# GCP Billing Kill-Switch — Deploy Runbook

Guarantees a hard $300 ceiling: a Cloud Function disables billing on the project
when the budget is exceeded. Budget alerts alone only email you — this actually stops spend.

> ⚠️ Caveat: GCP billing data lags a few hours, so set the budget BELOW $300 (e.g. $280)
> as a buffer. The switch is a safety net, not a to-the-cent cap.

## Prereqs
- gcloud installed (`gcloud --version`) and logged in (`gcloud auth login`).
- You are Billing Account Administrator on the billing account.

## Step 0 — set your variables (PowerShell)
```powershell
$PROJECT_ID   = "your-project-id"                 # from: gcloud projects list
$BILLING_ACCT = "XXXXXX-XXXXXX-XXXXXX"            # from: gcloud billing accounts list
$REGION       = "us-central1"
```

## Step 1 — enable APIs
```powershell
gcloud config set project $PROJECT_ID
gcloud services enable cloudbilling.googleapis.com cloudfunctions.googleapis.com `
  run.googleapis.com pubsub.googleapis.com cloudbuild.googleapis.com
```

## Step 2 — Pub/Sub topic the budget will publish to
```powershell
gcloud pubsub topics create billing-kill
```

## Step 3 — deploy the kill-switch function (run from this folder)
```powershell
cd C:\dev\_hub\gcp-killswitch
gcloud functions deploy billing-killswitch `
  --gen2 --runtime=python312 --region=$REGION `
  --source=. --entry-point=stop_billing `
  --trigger-topic=billing-kill `
  --set-env-vars=GCP_PROJECT_TO_DISABLE=$PROJECT_ID
```

## Step 4 — grant the function permission to disable billing
```powershell
$SA = gcloud functions describe billing-killswitch --gen2 --region=$REGION `
  --format="value(serviceConfig.serviceAccountEmail)"
echo "Function service account: $SA"
gcloud billing accounts add-iam-policy-binding $BILLING_ACCT `
  --member="serviceAccount:$SA" `
  --role="roles/billing.admin"
```

## Step 5 — wire your budget to the topic (Console)
Billing → **Budgets & alerts** → create/edit your budget →
- **Scope:** limit to this project (and optionally the Vertex AI service).
- **Amount:** **$280** (buffer under the ~$340 credit balance).
- ⚠️ **CRITICAL — Credits:** under the scope's **Credits** section, **UNCHECK / EXCLUDE**
  "Promotions and others" (and discounts). This makes the budget track **GROSS usage
  (before credits)**. If credits are INCLUDED, cost reads ~$0 until credits run out and
  the switch fires only AFTER you start paying real money — defeating the whole purpose.
- **Thresholds:** 50%, 90%, 100% (actual).
- **Manage notifications** → **Connect a Pub/Sub topic** → select **billing-kill** → Save.

### How it knows credits are used (mechanics)
The budget measures your Vertex AI **usage cost**. With credits EXCLUDED, that number =
gross usage, which equals how much of your credits you've burned. When it crosses $280,
the budget publishes to `billing-kill` → the function disables billing → hard stop.
Note: GCP billing data lags a few hours, so the switch isn't instant — that's why $280
(not $300) leaves a safety buffer.

## Test (safe)
Publish a fake over-budget message to confirm the wiring (this will DISABLE billing —
only run if you're ready to re-enable it after):
```powershell
# NOTE: in PowerShell, escape the inner double-quotes as \" or the JSON arrives malformed.
# SAFE under-budget test (no action taken):
gcloud pubsub topics publish billing-kill --message='{\"budgetDisplayName\":\"test\",\"costAmount\":100,\"budgetAmount\":24000}'
# check it ran with no action:
gcloud functions logs read billing-killswitch --gen2 --region=us-central1 --limit=8 --format="value(log)"
```
Then check Billing on the project — it should be detached. Re-enable manually in Console
(Billing → Link a billing account) to resume.

## After it ever fires
The project's billing is detached and all billable services stop. To resume: re-link the
billing account in the Console. Investigate what burned the budget first.
