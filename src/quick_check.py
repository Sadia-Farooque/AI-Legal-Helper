"""Hands-on model check (Sprint 5, D29): run your own messages through the app's model in one go.

Write one message per line in a text file (English, Roman Urdu or mixed; empty lines are skipped), then:

    python -m src.quick_check check.txt

It prints, for each message: answered or refused, the top-3 sections with confidence, and the legal condition
note if any. Nothing is saved. Keep check.txt out of git (it may contain private stories).
"""

import sys

from src.analyzer import analyze, legal_condition


def main(path):
    with open(path, encoding="utf-8") as f:
        msgs = [m.strip() for m in f if m.strip()]
    answered = 0
    for i, m in enumerate(msgs, 1):
        r = analyze(m)
        top = ", ".join(f"{c['section']} {c['name']} ({c['score']:.0%})" for c in r["results"])
        status = "ANSWER " if r["status"] == "ok" else "REFUSED"
        answered += r["status"] == "ok"
        print(f"\n{i:2d}. {m}\n    {status} | {top}")
        if r["status"] == "ok":
            note = legal_condition(r["results"][0]["section"], m)
            if note:
                print(f"    note: {note}")
    print(f"\n{answered}/{len(msgs)} answered, {len(msgs) - answered} refused (threshold 70%).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m src.quick_check check.txt")
        sys.exit(1)
    main(sys.argv[1])
