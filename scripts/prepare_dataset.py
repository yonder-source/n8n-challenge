import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "test_dataset.csv"
OUTPUT_JSONL = ROOT / "data" / "prepared_examples.jsonl"
OUTPUT_CANONICAL_CSV = ROOT / "data" / "test_dataset_canonical.csv"


def normalize_subject(subject: str) -> str:
    if not subject:
        return ""
    text = subject.strip()
    text = re.sub(r"^(re:|fwd:|fw:)\s*", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text)


def clean_body(body: str) -> str:
    if not body:
        return ""
    text = body.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:4000]


def sender_domain(from_email: str) -> str:
    if not from_email or "@" not in from_email:
        return "unknown"
    return from_email.split("@", 1)[1].lower().strip()


def detect_from_email_column(headers):
    for header in headers:
        lower = header.lower().strip()
        if lower == "from_email":
            return header
        if "drive.google.com" in lower:
            return header
    raise ValueError("Could not detect from_email column")


def main() -> None:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []
        from_email_col = detect_from_email_column(headers)

        rows = []
        for row in reader:
            canonical = {
                "email_id": row.get("email_id", "").strip(),
                "from_name": row.get("from_name", "").strip(),
                "from_email": row.get(from_email_col, "").strip(),
                "to_email": row.get("to_email", "").strip(),
                "subject": row.get("subject", "").strip(),
                "body": row.get("body", "").strip(),
                "expected_category": row.get("expected_category", "").strip(),
                "expected_action": row.get("expected_action", "").strip(),
            }
            canonical["subject_clean"] = normalize_subject(canonical["subject"])
            canonical["body_clean"] = clean_body(canonical["body"])
            canonical["sender_domain"] = sender_domain(canonical["from_email"])
            canonical["source_type"] = "email_example"
            canonical["split"] = "seed"
            canonical["language"] = "en"
            canonical["review_status"] = "approved_seed"
            canonical["reviewed_at"] = "2026-03-03"
            rows.append(canonical)

    canonical_headers = [
        "email_id",
        "from_name",
        "from_email",
        "to_email",
        "subject",
        "body",
        "expected_category",
        "expected_action",
        "subject_clean",
        "body_clean",
        "sender_domain",
        "source_type",
        "split",
        "language",
        "review_status",
        "reviewed_at",
    ]

    with OUTPUT_CANONICAL_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=canonical_headers,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    with OUTPUT_JSONL.open("w", encoding="utf-8") as file:
        for row in rows:
            payload = {
                "id": f"seed::{row['email_id']}",
                "text": f"Subject: {row['subject_clean']}\nBody: {row['body_clean']}\nSenderDomain: {row['sender_domain']}",
                "metadata": {
                    "email_id": row["email_id"],
                    "source_type": row["source_type"],
                    "split": row["split"],
                    "language": row["language"],
                    "sender_domain": row["sender_domain"],
                    "review_status": row["review_status"],
                    "reviewed_at": row["reviewed_at"]
                },
                "labels_for_eval_only": {
                    "expected_category": row["expected_category"],
                    "expected_action": row["expected_action"]
                }
            }
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(f"Prepared {len(rows)} rows")
    print(f"- canonical csv: {OUTPUT_CANONICAL_CSV}")
    print(f"- example jsonl: {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
