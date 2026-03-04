import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_JSONL = ROOT / "data" / "prepared_examples.jsonl"
OUTPUT_JSONL = ROOT / "data" / "embedding_requests_examples.jsonl"


def main() -> None:
    count = 0
    with INPUT_JSONL.open("r", encoding="utf-8") as source, OUTPUT_JSONL.open("w", encoding="utf-8") as out:
        for line in source:
            row = json.loads(line)
            request = {
                "id": row["id"],
                "namespace": "examples",
                "text": row["text"],
                "metadata": row["metadata"],
            }
            out.write(json.dumps(request, ensure_ascii=False) + "\n")
            count += 1

    print(f"Built {count} embedding requests to {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
