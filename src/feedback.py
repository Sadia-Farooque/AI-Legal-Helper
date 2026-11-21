"""Extra 3: "Was this correct?" feedback.

Where feedback goes
1. Always: appended to data/feedback/feedback.csv on the machine running the app (git-ignored: private).
2. If configured: also opened as a GitHub Issue labelled `feedback` in the project repo, so the team is
   notified and can discuss it. This matters after deployment, because free cloud hosts wipe local files on
   restart. Configure with environment variables (or Streamlit secrets):
       FEEDBACK_GITHUB_TOKEN = a GitHub token allowed to create issues
       FEEDBACK_GITHUB_REPO  = owner/repo   (default: abdulqudoos181005/AI-Legal-Helper-for-Pakistan)

Privacy: the incident text is stored ONLY if the user ticks consent. Corrections from people who say they are
lawyers or law students are kept as expert labels for future retraining (after manual checking).
"""

import csv
import json
import os
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FEEDBACK_CSV = os.path.join(PROJECT_ROOT, "data", "feedback", "feedback.csv")
COLUMNS = ["timestamp", "verdict", "predicted", "correct_sections", "role", "comment", "incident_text",
           "model", "status"]
DEFAULT_REPO = "abdulqudoos181005/AI-Legal-Helper-for-Pakistan"


def make_record(verdict, predicted, correct_sections, role, comment, incident_text, consent, model, status):
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": verdict,
        "predicted": json.dumps(predicted),
        "correct_sections": json.dumps(correct_sections),
        "role": role,
        "comment": (comment or "").strip()[:2000],
        "incident_text": (incident_text or "").strip()[:2000] if consent else "",
        "model": model,
        "status": status,
    }


def save_csv(record, path=FEEDBACK_CSV):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow(record)
    return path


def _config(secrets=None):
    secrets = secrets or {}
    token = os.environ.get("FEEDBACK_GITHUB_TOKEN") or secrets.get("FEEDBACK_GITHUB_TOKEN")
    repo = os.environ.get("FEEDBACK_GITHUB_REPO") or secrets.get("FEEDBACK_GITHUB_REPO") or DEFAULT_REPO
    return token, repo


def issue_body(record):
    lines = [f"**Verdict:** {record['verdict']}", f"**Role:** {record['role']}",
             f"**Predicted (top-3):** {record['predicted']}", f"**User says correct:** {record['correct_sections']}",
             f"**Model:** {record['model']} ({record['status']})", "", f"**Comment:** {record['comment'] or '-'}"]
    if record["incident_text"]:
        lines += ["", "**Incident (shared with consent):**", "> " + record["incident_text"].replace("\n", "\n> ")]
    lines += ["", "_Sent from the Incident Analyzer feedback form._"]
    return "\n".join(lines)


def open_issue(record, secrets=None, timeout=8):
    """Create a GitHub Issue for this feedback. Returns the issue URL, or None if not configured / failed."""
    token, repo = _config(secrets)
    if not token:
        return None
    import requests
    title = f"[feedback] {record['verdict']} from {record['role']}: predicted {json.loads(record['predicted'])[:1]}"
    try:
        r = requests.post(f"https://api.github.com/repos/{repo}/issues", timeout=timeout,
                          headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                          json={"title": title[:200], "body": issue_body(record), "labels": ["feedback"]})
        return r.json().get("html_url") if r.status_code in (200, 201) else None
    except Exception:  # noqa: BLE001 (network errors must never break the app)
        return None


def submit(record, secrets=None, path=FEEDBACK_CSV):
    saved = save_csv(record, path)
    return {"csv": saved, "issue_url": open_issue(record, secrets)}
