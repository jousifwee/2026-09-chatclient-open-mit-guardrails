#!/usr/bin/env python3
"""Erzeugt PROMPTS.md: alle Prompts dieses Projekts chronologisch, mit Zeitstempel und Modell.

Quelle sind die Claude-Code-Transcripts unter
~/.claude/projects/<kodierter-Projektpfad>/*.jsonl

Aufruf (aus dem Projektverzeichnis):
    python tools/collect_prompts.py
    python tools/collect_prompts.py --out docs/PROMPTS.md
    python tools/collect_prompts.py --logs "C:/Users/<user>/.claude/projects/<dir>"
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

MODEL_NAMES = {
    "claude-opus-5": "Opus 5",
    "claude-sonnet-5": "Sonnet 5",
    "claude-fable-5-1": "Fable 5.1",
    "claude-haiku-4-5-20251001": "Haiku 4.5",
}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def offset_label(dt):
    """z. B. 'UTC+02:00' - kompakter und eindeutiger als lange Zeitzonennamen."""
    off = dt.strftime("%z")
    return f"UTC{off[:3]}:{off[3:]}" if off else "UTC"


def encoded_project_dir(project_path):
    """Claude Code kodiert den Projektpfad, indem alles ausser [A-Za-z0-9] zu '-' wird."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project_path))


def default_log_dir(project_path):
    return os.path.join(
        os.path.expanduser("~"), ".claude", "projects", encoded_project_dir(project_path)
    )


def is_real_prompt(text):
    if not text or not text.strip():
        return False
    t = text.strip()
    skip_prefixes = (
        "<system-reminder>",
        "<local-command-stdout>",
        "<command-name>",
        "Caveat: The messages below",
        # Harness-Artefakt, kein Prompt: entsteht, wenn ein Werkzeugaufruf
        # abgebrochen wird, und wuerde das Protokoll verfaelschen.
        "[Request interrupted",
    )
    return not t.startswith(skip_prefixes)


def clean(text):
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    return text.strip()


def message_text(msg):
    content = msg.get("content")
    if isinstance(content, list):
        return "\n".join(
            c.get("text", "")
            for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        )
    return content or ""


def collect(log_dir):
    entries = []
    for path in sorted(glob.glob(os.path.join(log_dir, "*.jsonl"))):
        session = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        for i, row in enumerate(rows):
            if row.get("type") != "user" or row.get("isMeta"):
                continue
            text = clean(message_text(row.get("message") or {}))
            if not is_real_prompt(text):
                continue
            # Modell aus der ersten darauffolgenden Assistant-Antwort
            model = next(
                (
                    (r.get("message") or {}).get("model")
                    for r in rows[i + 1 :]
                    if r.get("type") == "assistant"
                ),
                None,
            )
            # Der letzte Prompt kann noch unbeantwortet sein (laufender Turn):
            # dann das zuletzt in dieser Session genutzte Modell annehmen.
            pending = model is None
            if pending:
                model = next(
                    (
                        (r.get("message") or {}).get("model")
                        for r in reversed(rows[:i])
                        if r.get("type") == "assistant"
                    ),
                    None,
                )
            ts = row.get("timestamp")
            entries.append(
                {
                    "dt": datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None,
                    "session": session,
                    "text": text,
                    "model": model,
                    "pending": pending,
                }
            )
    entries.sort(key=lambda e: e["dt"] or datetime.min.replace(tzinfo=timezone.utc))
    return entries


def render(entries):
    now = datetime.now().astimezone()
    tzlabel = offset_label(now)
    lines = [
        "# Prompt-Protokoll",
        "",
        f"Projekt: `{os.path.basename(PROJECT_ROOT)}`",
        "",
        "Chronologische Liste aller Prompts (Nutzereingaben) in diesem Projekt, inkl.",
        "Zeitstempel und dem fuer die jeweilige Antwort genutzten Modell. Zeiten in lokaler",
        "Zeitzone, UTC zusaetzlich angegeben.",
        "",
        f"Generiert von `tools/collect_prompts.py` am "
        f"{now.strftime('%Y-%m-%d %H:%M')} ({tzlabel}) - {len(entries)} Prompt(s)",
        "",
        "---",
        "",
    ]
    for n, e in enumerate(entries, 1):
        local = e["dt"].astimezone()
        utc = e["dt"].astimezone(timezone.utc)
        model_id = e["model"] or "unbekannt"
        model = MODEL_NAMES.get(model_id, model_id)
        lines += [
            f"## {n}. {local.strftime('%Y-%m-%d %H:%M:%S')} ({offset_label(local)})",
            "",
            f"- **UTC:** {utc.strftime('%Y-%m-%d %H:%M:%S')}Z",
            f"- **Modell:** {model} (`{model_id}`)"
            + (" - Session-Modell, Antwort lag beim Generieren noch nicht im Transcript"
               if e.get("pending") else ""),
            f"- **Session:** `{e['session']}`",
            "",
            "**Prompt:**",
            "",
        ]
        for pl in e["text"].splitlines() or [""]:
            lines.append(f"> {pl}" if pl.strip() else ">")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--logs", default=None, help="Verzeichnis mit den *.jsonl-Transcripts")
    ap.add_argument("--out", default=os.path.join(PROJECT_ROOT, "PROMPTS.md"), help="Zieldatei")
    args = ap.parse_args()

    log_dir = args.logs or default_log_dir(PROJECT_ROOT)
    if not os.path.isdir(log_dir):
        sys.exit(f"Transcript-Verzeichnis nicht gefunden: {log_dir}")

    entries = collect(log_dir)
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(entries))
    print(f"{len(entries)} Prompt(s) -> {out}")


if __name__ == "__main__":
    main()
