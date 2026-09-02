---
name: prompt-protokoll-tooling
description: In diesem Projekt wird ein Prompt-Protokoll (PROMPTS.md) aus den Claude-Code-Transcripts per tools/collect_prompts.py generiert.
metadata:
  type: project
---

Der Nutzer will die Prompt-Historie dieses Projekts dokumentiert haben: `PROMPTS.md` im
Projektwurzelverzeichnis, chronologisch, mit lokalem Zeitstempel, UTC, genutztem Modell und
Session-ID. Erzeugt wird sie von `tools/collect_prompts.py` (liest
`~/.claude/projects/<kodierter-Projektpfad>/*.jsonl`), Datei wird bei jedem Lauf komplett neu
geschrieben.

**Why:** Passt zum Lernziel [[projektziel-guardrails-lernen]] - die eigene Interaktion mit dem
Agenten wird selbst zur nachvollziehbaren, agentenlesbaren Dokumentation.

**How to apply:** Nach nennenswerten neuen Prompts `python tools/collect_prompts.py` laufen
lassen, statt `PROMPTS.md` von Hand zu editieren. Handaenderungen wuerden beim naechsten Lauf
verworfen.
